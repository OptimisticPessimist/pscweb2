from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login

from .forms import CustomUserCreationForm


class SignUpView(generic.CreateView):
    """
    ユーザー登録ビュー
    """
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('production:prod_list')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        """
        フォームのバリデーションが通った場合に呼ばれる。
        ユーザーを保存し、ログインさせてからリダイレクトする。
        """
        self.object = form.save()

        login(self.request, self.object)

        return super().form_valid(form)
