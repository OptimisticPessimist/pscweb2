from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.db.models import Q
from production.models import Production, ProdUser
from script.models import Script
from .view_func import *


class ScriptList(LoginRequiredMixin, ListView):
    '''Script のリストビュー
    '''
    model = Script
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        # 公開されている台本と、所有している台本を表示
        return Script.objects.filter(
            Q(public_level=2) | Q(owner=self.request.user))


class ScriptCreate(LoginRequiredMixin, CreateView):
    '''Script の追加ビュー
    '''
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 保存するレコード
        new_scrpt = form.save(commit=False)
        # アクセス中のユーザを所有者にする
        new_scrpt.owner = self.request.user

        messages.success(self.request, str(new_scrpt) + " を作成しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ScriptUpdate(LoginRequiredMixin, UpdateView):
    '''Script の更新ビュー
    '''
    model = Script
    fields = ('title', 'author', 'public_level', 'format', 'raw_data')
    success_url = reverse_lazy('script:scrpt_list')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # 所有者でなければアクセス不可
        if self.request.user != self.get_object().owner:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # 所有者でなければアクセス不可
        if self.request.user != self.get_object().owner:
            raise PermissionDenied
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        messages.success(self.request, str(form.instance) + " を更新しました。")
        return super().form_valid(form)

    def form_invalid(self, form):
        '''更新に失敗した時
        '''
        messages.warning(self.request, "更新できませんでした。")
        return super().form_invalid(form)


class ScriptDetail(LoginRequiredMixin, DetailView):
    '''Script の詳細ビュー
    '''
    model = Script
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if self.request.user != self.get_object().owner\
            and self.get_object().public_level != 2:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)


class ProdFromScript(LoginRequiredMixin, CreateView):
    '''Script データを元に Production を作成するビュー
    '''
    model = Production
    fields = ('name',)
    template_name = 'script/production_from_script.html'
    success_url = reverse_lazy('production:prod_list')
    
    # TODO: post リクエスト時も、所有・公開をチェックするべき。
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # URLconf から、Script を取得し、属性として持っておく
        scripts = Script.objects.filter(pk=self.kwargs['scrpt_id'])
        if scripts.count() < 1:
            raise Http404
        self.script = scripts[0]
        
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if self.request.user != self.script.owner\
            and self.script.public_level != 2:
            raise PermissionDenied

        return super().get(request, *args, **kwargs)
    
    def get_initial(self):
        '''フォームのフィールドの初期値をオーバーライド
        '''
        initial = super().get_initial()
        # GET リクエスト中に呼ばれた場合は script 属性で初期化
        if self.request.method == 'GET':
            initial['name'] = self.script.title
        return initial
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 保存したレコードを取得する
        new_prod = form.save(commit=True)
        
        # 自分を owner として公演ユーザに追加する
        prod_user = ProdUser(production=new_prod, user=self.request.user,
            is_owner=True)
        prod_user.save()
        
        # POST で取得した URLconf
        scrpt_id = self.kwargs['scrpt_id']
        # 台本を元に、公演にデータを追加する
        add_data_from_script(new_prod.id, scrpt_id)
        
        messages.success(self.request, str(new_prod) + " を作成しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ScriptViewer(LoginRequiredMixin, DetailView):
    '''Script データから作った HTML を表示するビュー
    '''

    model = Script

    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # 所有者でもなく、公開もされていなければ、アクセス不可
        if self.request.user != self.get_object().owner\
            and self.get_object().public_level != 2:
            raise PermissionDenied
        
        html = html_from_fountain(self.get_object().raw_data)
        return HttpResponse(html)
