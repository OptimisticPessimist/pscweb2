from typing import Any

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
from django.utils.html import escape
from production.models import Production, ProdUser
from script.models import Script
from .view_func import *

# --- PDF生成に必要なライブラリ ---
import weasyprint  # xhtml2pdf の代わりに weasyprint をインポート


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
        if self.request.user != self.get_object().owner \
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
        if self.request.user != self.get_object().owner \
                and self.get_object().public_level != 2:
            raise PermissionDenied

        html = html_from_fountain(self.get_object().raw_data)
        return HttpResponse(html)


class ScriptPDFDownloadView(LoginRequiredMixin, View):
    """
        台本データをPDFとしてダウンロードさせるビュー (WeasyPrintを使用)
        """

    def get(self, request, *args, **kwargs):
        script = get_object_or_404(Script, pk=self.kwargs['pk'])

        # 所有者でもなく、公開もされていなければアクセス不可
        if request.user != script.owner and script.public_level != 2:
            raise PermissionDenied

        try:
            # 1. 既存の関数を使い、台本データからHTML文字列を生成
            html_string = html_from_fountain(script.raw_data)

            # 2. 縦書きと日本語フォント用のCSSを定義
            #    WeasyPrintはWebフォントの扱いに優れているため、Google Fontsを直接参照します。
            font_css = """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&display=swap');

                    html {
                        font-family: 'Noto Serif JP', serif;
                        font-size: 12pt;
                        /* 縦書き設定 */
                        writing-mode: vertical-rl;
                    }
                    body {
                        /* A4縦(210x297mm)を横にして縦書き用紙として使う */
                        width: 297mm;
                        height: 210mm;
                        margin: 20mm;
                    }
                    h1 {
                        font-size: 24pt;
                        text-align: center;
                        /* 縦書きではmargin-rightが上方向のマージンになる */
                        margin-right: 1em;
                    }
                    div {
                        margin-bottom: 1em;
                    }
                </style>
                """
            # 生成したHTMLの<head>タグの直後にCSSを挿入
            html_with_style = html_string.replace('</head>', f'{font_css}</head>')

            # 3. WeasyPrintを使ってHTMLからPDFを生成
            html = weasyprint.HTML(string=html_with_style)
            pdf_data = html.write_pdf()

            # 4. HttpResponseで返す
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{script.title}.pdf"'
            return response

        except Exception as e:
            # もし万が一エラーが発生した場合に、その内容を画面に表示する
            error_message = f"<h1>PDF Generation Error</h1>"
            error_message += f"<p>An unexpected error occurred during PDF generation.</p>"
            error_p_style = "background-color: #fbeae5; border: 1px solid #f4a2a2; padding: 10px; border-radius: 5px; font-family: monospace;"
            error_message += f"<p style='{error_p_style}'><strong>Error Type:</strong> {type(e).__name__}<br>"
            error_message += f"<strong>Error Message:</strong> {escape(str(e))}</p>"
            error_message += f"<p>Please report this error message to the developer.</p>"
            return HttpResponse(error_message, status=500)
