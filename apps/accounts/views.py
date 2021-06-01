from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import LoginForm


class Login(LoginView):
    """
    Handles user authentication.
    """

    template_name = "login.html"
    authentication_form = LoginForm

    def get_success_url(self) -> str:
        """
        Returns the redirect URL upon successful login.
        """
        if self.request.user.is_borrower:
            return reverse_lazy("lending:loans-active")

        return reverse_lazy("dashboard")
