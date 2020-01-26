from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from rehearsal.views.view_func import *
from .models import Production, ProdUser


class ProdList(LoginRequiredMixin, ListView):
    '''Production のリストビュー
    
    ログインユーザの公演のみ表示するため、モデルは ProdUser
    '''
    model = ProdUser
    template_name = 'production/production_list.html'
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        # 自分である ProdUser を取得する
        prod_users = ProdUser.objects.filter(user=self.request.user)
        return prod_users


class ProdCreate(LoginRequiredMixin, CreateView):
    '''Production の追加ビュー
    '''
    model = Production
    fields = ('name',)
    success_url = reverse_lazy('production:prod_list')
    
    def form_valid(self, form):
        '''バリデーションを通った時
        '''
        # 保存したレコードを取得する
        new_prod = form.save(commit=True)
        
        # 自分を owner として公演ユーザに追加する
        prod_user = ProdUser(production=new_prod, user=self.request.user,
            is_owner=True)
        prod_user.save()
        
        messages.success(self.request, str(new_prod) + " を作成しました。")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        '''追加に失敗した時
        '''
        messages.warning(self.request, "作成できませんでした。")
        return super().form_invalid(form)


class ProdUpdate(LoginRequiredMixin, UpdateView):
    '''Production の更新ビュー
    '''
    model = Production
    fields = ('name',)
    success_url = reverse_lazy('production:prod_list')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, kwargs['pk'])
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, kwargs['pk'])
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
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


class ProdDelete(LoginRequiredMixin, DeleteView):
    '''Production の削除ビュー
    '''
    model = Production
    template_name_suffix = '_delete'
    success_url = reverse_lazy('production:prod_list')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, kwargs['pk'])
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, kwargs['pk'])
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        
        return super().post(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result


class UsrList(LoginRequiredMixin, ListView):
    '''ProdUser のリストビュー
    '''
    model = ProdUser
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_user = accessing_prod_user(self, kwargs['prod_id'])
        if not prod_user:
            raise PermissionDenied
        
        # テンプレートから参照できるよう、ビューの属性にしておく
        self.prod_user = prod_user
        
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        '''リストに表示するレコードをフィルタする
        '''
        prod_id=self.kwargs['prod_id']
        prod_users = ProdUser.objects.filter(production__pk=prod_id)
        return prod_users
    
    def get_context_data(self, **kwargs):
        '''テンプレートに渡すパラメタを改変する
        '''
        context = super().get_context_data(**kwargs)
        
        # 戻るボタン用の prod_id をセット
        context['prod_id'] = self.kwargs['prod_id']
        
        return context


class UsrUpdate(LoginRequiredMixin, UpdateView):
    '''ProdUser の更新ビュー
    '''
    model = ProdUser
    fields = ('is_editor',)
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_id = self.get_object().production.id
        prod_user = accessing_prod_user(self, prod_id)
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        
        # テンプレートから参照できるよう、ビューの属性にしておく
        self.prod_user = prod_user
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_id = self.get_object().production.id
        prod_user = accessing_prod_user(self, prod_id)
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''追加に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('production:usr_list', kwargs={'prod_id': prod_id})
        return url
    
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


class UsrDelete(LoginRequiredMixin, DeleteView):
    '''ProdUser の削除ビュー
    '''
    model = ProdUser
    template_name_suffix = '_delete'
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_id = self.get_object().production.id
        prod_user = accessing_prod_user(self, prod_id)
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        # 自分自身を削除することはできない
        if self.get_object() == prod_user:
            raise PermissionDenied
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        '''保存時のリクエストを受けるハンドラ
        '''
        # アクセス情報から公演ユーザを取得しアクセス権を検査する
        prod_id = self.get_object().production.id
        prod_user = accessing_prod_user(self, prod_id)
        if not prod_user:
            raise PermissionDenied
        # 所有権を持っていなければアクセス拒否
        if not (prod_user.is_owner):
            raise PermissionDenied
        # 自分自身を削除することはできない
        if self.get_object() == prod_user:
            raise PermissionDenied
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        '''削除に成功した時の遷移先を動的に与える
        '''
        prod_id = self.object.production.id
        url = reverse_lazy('production:usr_list', kwargs={'prod_id': prod_id})
        return url
    
    def delete(self, request, *args, **kwargs):
        '''削除した時のメッセージ
        '''
        result = super().delete(request, *args, **kwargs)
        messages.success(
            self.request, str(self.object) + " を削除しました。")
        return result
