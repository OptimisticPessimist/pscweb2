from typing import Any
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404

from production.models import Production, ProdUser
from ..models import Script
from .view_func import html_from_fountain, html_from_sp_yaml, add_data_from_script


class ScriptList(LoginRequiredMixin, ListView):
    """台本の一覧を表示するビュー"""
    model = Script

    def get_queryset(self):
        # 公開されている台本と、自分が所有者の台本のみ表示
        return Script.objects.select_related('owner').filter(
            Q(public_level=2) | Q(owner=self.request.user)
        )


class ScriptCreate(LoginRequiredMixin, CreateView):
    """台本を新規作成するビュー"""
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')

    def form_valid(self, form):
        new_script = form.save(commit=False)
        new_script.owner = self.request.user
        new_script.save()
        messages.success(self.request, f"'{new_script.title}' を作成しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ScriptUpdate(LoginRequiredMixin, UpdateView):
    """台本を編集するビュー"""
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user != obj.owner:
            raise PermissionDenied
        return obj

    def form_valid(self, form):
        messages.success(self.request, f"'{form.instance.title}' を更新しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class ScriptDetail(LoginRequiredMixin, DetailView):
    """台本の詳細を表示するビュー"""
    model = Script

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user != obj.owner and obj.public_level != 2:
            raise PermissionDenied
        return obj


class ScriptViewer(LoginRequiredMixin, DetailView):
    """台本をHTMLでプレビューするビュー"""
    model = Script

    def get(self, request, *args, **kwargs):
        script_obj = self.get_object()
        if request.user != script_obj.owner and script_obj.public_level != 2:
            raise PermissionDenied

        if script_obj.format == 1:  # Fountain
            html = html_from_fountain(script_obj.raw_data)
        elif script_obj.format == 2:  # sp.yaml
            html = html_from_sp_yaml(script_obj.raw_data)
        else:
            html = "<h1>Unsupported Format</h1><p>この台本形式はプレビューに対応していません。</p>"
        return HttpResponse(html)


class ProdFromScript(LoginRequiredMixin, CreateView):
    """台本から公演を作成するビュー"""
    model = Production
    fields = ('name',)
    template_name = 'script/production_from_script.html'
    success_url = reverse_lazy('production:prod_list')

    def dispatch(self, request, *args, **kwargs):
        self.script = get_object_or_404(Script, pk=self.kwargs['scrpt_id'])
        if request.user != self.script.owner and self.script.public_level != 2:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['name'] = self.script.title
        return initial

    def form_valid(self, form):
        new_prod = form.save()
        ProdUser.objects.create(
            production=new_prod,
            user=self.request.user,
            is_owner=True
        )
        add_data_from_script(new_prod.id, self.script.id)
        messages.success(self.request, f"'{new_prod.name}' を作成しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)
