from django import forms
from django.contrib.auth import get_user_model
from .models import ProdUser, Invitation
import accounts


class ProdUserAdminForm(forms.ModelForm):
    '''管理サイトで公演ユーザを編集する時のフォーム
    '''
    class Meta:
        model = ProdUser
        fields = ('production', 'user', 'is_owner', 'is_editor')

    def clean_user(self):
        '''ユーザのバリデーション
        
        user を検証しているという事は、追加フォームである
        '''
        # 追加しようとしている user
        user = self.cleaned_data['user']
        
        # prod_id が入力されていなければ、そっちで検証されるのでスルー
        if 'production' not in self.cleaned_data:
            return user
        
        # 同じ production, user のレコードがあるか検索
        production = self.cleaned_data['production']
        dupe = ProdUser.objects.filter(production=production, user=user)
        
        # 追加なので、同じ production, user のレコードが見つかったら重複
        if len(dupe) > 0:
            raise forms.ValidationError('{} はすでに {} のユーザです。'
                .format(user, production))
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


class InvtForm(forms.ModelForm):
    '''座組への招待の追加フォーム
    '''
    class Meta:
        model = Invitation
        fields = ('invitee',)
    
    def __init__(self, *args, **kwargs):
        # view で追加したパラメタを抜き取る
        production = kwargs.pop('production')
        
        super().__init__(*args, **kwargs)
        
        # 招待される人は、公演ユーザ以外かつ招待中でないこと
        
        # 公演ユーザのユーザ ID リスト
        prod_users = ProdUser.objects.filter(production=production)
        prod_user_user_ids = [prod_user.user.id for prod_user in prod_users]
        # 招待中のユーザの ID リスト
        invitations = Invitation.objects.filter(production=production)
        current_invitee_ids = [invt.invitee.id for invt in invitations]
        
        # 公演ユーザと招待中のユーザを除いたユーザ
        user_model = get_user_model()
        invitee_choice = user_model.objects.exclude(id__in=prod_user_user_ids)\
            .exclude(id__in=current_invitee_ids).order_by('username')
        
        self.fields['invitee'].queryset = invitee_choice
