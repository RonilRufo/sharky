from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class Dashboard(LoginRequiredMixin, TemplateView):
    """
    Displays the dashboard page.
    """
    template_name = "index.html"
