from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login
from django.shortcuts import redirect

# 作成したカスタムフォームをインポート
from .forms import CustomUserCreationForm


class SignUpView(generic.CreateView):
    """
    ユーザー登録ビュー
    """
    # 使用するフォームをカスタムフォームに変更
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('production:prod_list')  # 登録後のリダイレクト先
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        """
        フォームのバリデーションが通った場合に呼ばれる。
        ユーザーを保存し、ログインさせてからリダイレクトする。
        """
        user = form.save()
        login(self.request, user)
        return redirect(self.get_success_url())
