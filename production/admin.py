from django.contrib import admin
from .models import Production, ProdUser, Invitation
from .forms import ProdUserAdminForm


class ProdUserAdmin(admin.ModelAdmin):
    '''管理サイトで公演ユーザを表示する時の設定
    '''
    list_display = ('__str__', 'production', 'user', 'is_owner', 'is_editor')
    list_filter = ('production',)
    
    # バリデーションのためのカスタムフォーム
    form = ProdUserAdminForm
    
    # fields は Form の Meta でも定義しているが、表示順を維持するため
    fields = ('production', 'user', 'is_owner', 'is_editor')

    def add_view(self,request,extra_content=None):
        '''追加フォームでは全 field が変更できる
        '''
        self.readonly_fields = ()
        return super(ProdUserAdmin,self).add_view(request)

    def change_view(self,request,object_id,extra_content=None):
        '''変更フォームでは公演とユーザは変更できない
        '''
        self.readonly_fields = ('production','user')
        return super(ProdUserAdmin, self).change_view(request, object_id)


admin.site.register(Production)
admin.site.register(ProdUser, ProdUserAdmin)
admin.site.register(Invitation)
