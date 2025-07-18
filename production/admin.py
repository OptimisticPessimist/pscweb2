from django.contrib import admin
from .models import Production, ProdUser, Invitation
from .forms import ProdUserAdminForm


class ProdUserAdmin(admin.ModelAdmin):
    """管理サイトで公演ユーザを表示する時の設定"""
    list_display = ('__str__', 'production', 'user', 'is_owner', 'is_editor')
    list_filter = ('production',)

    form = ProdUserAdminForm
    fields = ('production', 'user', 'is_owner', 'is_editor')

    def add_view(self, request, extra_content=None):
        """追加フォームでは全 field が変更できる"""
        self.readonly_fields = ()
        # Python 3 スタイルの super() に修正
        return super().add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        """変更フォームでは公演とユーザは変更できない"""
        self.readonly_fields = ('production', 'user')
        # Python 3 スタイルの super() に修正
        return super().change_view(request, object_id)


admin.site.register(Production)
admin.site.register(ProdUser, ProdUserAdmin)
admin.site.register(Invitation)