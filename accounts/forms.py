from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    """
    カスタムユーザーモデル（accounts.User）に対応したユーザー登録フォーム。
    """

    class Meta(UserCreationForm.Meta):
        # settings.AUTH_USER_MODEL で指定されたモデル（accounts.User）を取得して設定する
        model = get_user_model()
        # 登録フォームに表示するフィールド。必要に応じて 'email' などを追加できます。
        fields = ('username',)
