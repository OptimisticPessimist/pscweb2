from django import forms
from django.contrib.auth import get_user_model
from .models import ProdUser, Invitation
import accounts


class ProdUserAdminForm(forms.ModelForm):
    """管理サイトで公演ユーザを編集する時のフォーム"""

    class Meta:
        model = ProdUser
        fields = ('production', 'user', 'is_owner', 'is_editor')

    def clean_user(self):
        """ユーザのバリデーション"""
        user = self.cleaned_data.get('user')
        production = self.cleaned_data.get('production')

        if not user or not production:
            return user

        # .exists() を使うと、レコードの有無だけを効率的に確認できます
        is_duplicate = ProdUser.objects.filter(production=production, user=user).exists()

        if is_duplicate:
            raise forms.ValidationError(f'{user} はすでに {production} のユーザです。')
        return user


# Production 新規作成時の処理をオーバーライドするサンプルコード
#
# from .models import Production
#
# class ProdCreateForm(forms.ModelForm):
#     '''Production の追加フォームをカスタマイズ
#     '''
#     class Meta:
#         model = Production
#         fields = ('name',)
#     
#     def save(self, commit=True):
#         '''保存時の処理をオーバーライド
#         '''
#         # 保存するべきものを取得する
#         m = super().save(commit=False)
#         
#         # 何らかの処理 (本来はデータを加工したりするところ)
#         print('ProdCreateForm.save()', self.user)
#         
#         if commit:
#             m.save()
#         return m
