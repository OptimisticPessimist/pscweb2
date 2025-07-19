from typing import Any
import yaml

from django.views import View
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
from rehearsal.models import Character, Scene, Appearance
from script.fountain import fountain
from script.models import Script
from .view_func import data_from_sp_yaml, html_from_sp_yaml, add_data_from_script, data_from_fountain


def html_from_fountain(text):
    '''Fountain フォーマットの台本から HTML を生成
    '''
    # パース
    f = fountain.Fountain(string=text)

    # コンテンツ生成
    content = ''
    # タイトル
    if 'title' in f.metadata:
        for title in f.metadata['title']:
            content += f'<h1>{title}</h1>'
    # 著者
    if 'author' in f.metadata:
        for author in f.metadata['author']:
            content += f'<div style="text-align:right;">{author}</div>'

    content += '<hr>'

    for e in f.elements:
        if e.element_type == 'Scene Heading':
            content += f'<h2>{e.element_text}</h2>'
        elif e.element_type == 'Action':
            if e.is_centered:
                content += f'<p style="text-align:center;">{e.element_text}</p>'
            else:
                content += f'<p>{e.element_text}</p>'
        elif e.element_type == 'Character':
            content += f'<p><strong>{e.element_text}</strong></p>'
        elif e.element_type == 'Dialogue':
            dialogue_html = e.element_text.replace('\n', '<br>')
            content += f'<div style="margin-left: 2em;">{dialogue_html}</div>'
        elif e.element_type == 'Parenthetical':
            content += f'<div style="margin-left: 2em; color: gray;">{e.element_text}</div>'
        elif e.element_type == 'Transition':
            content += f'<p style="text-align: right;"><em>{e.element_text.upper()}</em></p>'
        elif e.element_type == 'Section Heading':
            content += f'<h3 style="margin-top: 2em;">{e.element_text}</h3>'
        elif e.element_type == 'Page Break':
            content += '<hr style="margin: 2em 0;">'
        elif e.element_type == 'Empty Line':
            content += '<br>'
        # Synopsis, Comment, Boneyard はビューアでは無視

    # HTML全体を組み立てる
    html = f"""<html lang="ja">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
            <style>
                body {{ line-height: 1.6; font-family: sans-serif; }}
                h1, h2, h3 {{ margin-top: 1.5em; margin-bottom: 0.5em; }}
                p {{ margin: 0.5em 0; }}
            </style>
        </head>
        <body>{content}</body>
    </html>"""
    return html


class ScriptList(LoginRequiredMixin, ListView):
    """Script のリストビュー
    """
    model = Script

    def get_queryset(self):
        """リストに表示するレコードをフィルタする
        """
        # 公開されている台本と、所有している台本を表示
        return Script.objects.select_related('owner').filter(
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
        new_scrpt.save()

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

    def get_object(self, queryset=None):
        """オブジェクトを取得する際に権限チェックを行う"""
        obj = super().get_object(queryset)
        if self.request.user != obj.owner:
            raise PermissionDenied
        return obj

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

    def get_object(self, queryset=None):
        """オブジェクトを取得する際に権限チェックを行う"""
        obj = super().get_object(queryset)
        if self.request.user != obj.owner and obj.public_level != 2:
            raise PermissionDenied
        return obj


class ProdFromScript(LoginRequiredMixin, CreateView):
    """Script データを元に Production を作成するビュー
    """
    model = Production
    fields = ('name',)
    template_name = 'script/production_from_script.html'
    success_url = reverse_lazy('production:prod_list')

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
        initial['name'] = self.script.title
        return initial

    def form_valid(self, form):
        """バリデーションを通った時"""
        new_prod = form.save()

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
        script_obj = self.get_object()
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if request.user != script_obj.owner and script_obj.public_level != 2:
            raise PermissionDenied

        if script_obj.format == 1:  # Fountain
            html = html_from_fountain(script_obj.raw_data)
        elif script_obj.format == 2:  # sp.yaml
            html = html_from_sp_yaml(script_obj.raw_data)
        else:
            html = "<h1>Unsupported Format</h1><p>この台本形式はプレビューに対応していません。</p>"

        return HttpResponse(html)
