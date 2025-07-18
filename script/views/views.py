from typing import Any

from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from production.models import Production, ProdUser
from script.models import Script
from .view_func import *


class ScriptList(LoginRequiredMixin, ListView):
    """Script のリストビュー
    """
    model = Script
    
    def get_queryset(self):
        """リストに表示するレコードをフィルタする
        """
        # 公開されている台本と、所有している台本を表示
        return Script.objects.filter(
            Q(public_level=2) | Q(owner=self.request.user))


class ScriptCreate(LoginRequiredMixin, CreateView):
    """Script の追加ビュー
    """
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')
    
    def form_valid(self, form):
        """バリデーションを通った時
        """
        # 保存するレコード
        new_scrpt = form.save(commit=False)
        # アクセス中のユーザを所有者にする
        new_scrpt.owner = self.request.user

        messages.success(self.request, str(new_scrpt) + " を作成しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """追加に失敗した時
        """
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ScriptUpdate(LoginRequiredMixin, UpdateView):
    """Script の更新ビュー
    """
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')
    
    def get(self, request, *args, **kwargs):
        """表示時のリクエストを受けるハンドラ
        """
        # 所有者でなければアクセス不可
        if self.request.user != self.get_object().owner:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """保存時のリクエストを受けるハンドラ
        """
        # 所有者でなければアクセス不可
        if self.request.user != self.get_object().owner:
            raise PermissionDenied
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        """バリデーションを通った時
        """
        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        """更新に失敗した時
        """
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class ScriptDetail(LoginRequiredMixin, DetailView):
    """Script の詳細ビュー
    """
    model = Script
    
    def get(self, request, *args, **kwargs):
        """表示時のリクエストを受けるハンドラ
        """
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if self.request.user != self.get_object().owner\
            and self.get_object().public_level != 2:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)


class ProdFromScript(LoginRequiredMixin, CreateView):
    """Script データを元に Production を作成するビュー
    """
    model = Production
    fields = ('name',)
    template_name = 'script/production_from_script.html'
    success_url = reverse_lazy('production:prod_list')
    
    # TODO: post リクエスト時も、所有・公開をチェックするべき。

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.script = None

    def dispatch(self, request, *args, **kwargs):
        """GETとPOSTの両方で最初に呼ばれるメソッドで権限チェックを行う"""
        self.script = get_object_or_404(Script, pk=self.kwargs['scrpt_id'])

        # 所有者でもなく、公開もされていなければ、アクセス不可
        if request.user != self.script.owner and self.script.public_level != 2:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """フォームのフィールドの初期値をオーバーライド
        """
        initial = super().get_initial()
        # GET リクエスト中に呼ばれた場合は script 属性で初期化
        if self.request.method == 'GET':
            initial['name'] = self.script.title
        return initial

    def form_valid(self, form):
        """バリデーションを通った時"""
        # form.save()は、裏で new_prod.save() を呼んでいます
        new_prod = form.save()

        # .create() を使うと、インスタンス化と保存を同時に行えます
        ProdUser.objects.create(
            production=new_prod,
            user=self.request.user,
            is_owner=True
        )

        # 台本を元に、公演にデータを追加する
        add_data_from_script(new_prod.id, self.script.id)

        messages.success(self.request, f"{new_prod} を作成しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """追加に失敗した時
        """
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ScriptViewer(LoginRequiredMixin, DetailView):
    """Script データから作った HTML を表示するビュー
    """

    model = Script

    def get(self, request, *args, **kwargs):
        """表示時のリクエストを受けるハンドラ
        """
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if self.request.user != self.get_object().owner\
            and self.get_object().public_level != 2:
            raise PermissionDenied
        
        html = html_from_fountain(self.get_object().raw_data)
        return HttpResponse(html)
