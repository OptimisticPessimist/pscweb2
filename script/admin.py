from django.contrib import admin
from .models import Script


class ScriptAdmin(admin.ModelAdmin):
    '''管理サイトで台本を表示する時の設定
    '''
    list_display = ('__str__', 'create_dt', 'modify_dt', 'public_level')


admin.site.register(Script, ScriptAdmin)
