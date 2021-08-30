from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from .forms import CustomSetPasswordForm, LoginForm


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
            return reverse_lazy(
                "lending:borrowers-detail",
                args=(self.request.user.pk,),
            )

        return reverse_lazy("dashboard")


class PasswordChange(LoginRequiredMixin, FormView):
    """
    Enables user to change his/her current password.
    """

    form_class = CustomSetPasswordForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("lending:loans-active")

    def get_form_kwargs(self):
        context = super(PasswordChange, self).get_form_kwargs()
        context["user"] = self.request.user
        return context

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, _("Successfully set new password."))
        return super().form_valid(form)
