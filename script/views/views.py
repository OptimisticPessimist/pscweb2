from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from production.models import Production, ProdUser
from script.models import Script


class ScriptList(LoginRequiredMixin, ListView):
    '''Script のリストビュー
    '''
    model = Script
    
    def list_entries(self):
        return Script.objects.values('id', 'title', 'author', 'create_dt',
            'modify_dt', 'owner__id', 'owner__username')


class ScriptDetail(LoginRequiredMixin, DetailView):
    '''Script の詳細ビュー
    '''
    model = Script


class ProdFromScript(LoginRequiredMixin, CreateView):
    '''Script データを元に Production を作成するビュー
    '''
    model = Production
    fields = ('name',)
    template_name = 'script/production_from_script.html'
    success_url = reverse_lazy('production:prod_list')
    
    def get(self, request, *args, **kwargs):
        '''表示時のリクエストを受けるハンドラ
        '''
        # URLconf から、Script を取得し、属性として持っておく
        scripts = Script.objects.filter(pk=self.kwargs['scrpt_id'])
        if len(scripts) < 1:
            raise Http404
        self.script = scripts[0]
    
        return super().get(request, *args, **kwargs)

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

