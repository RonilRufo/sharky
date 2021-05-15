import math
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, F, Q, Sum, When
from django.utils import timezone
from django.views.generic import TemplateView

from apps.lending.models import Amortization, CapitalSource, Loan


class Dashboard(LoginRequiredMixin, TemplateView):
    """
    Displays the dashboard page.
    """
    template_name = "index.html"

    def get_active_loans(self) -> int:
        """
        Returns the number of active loans.
        """
        return Loan.objects.filter(is_completed=False).count()

    def get_earnings_for_current_month(self) -> int:
        """
        Returns the earnings from all loans for the current month.
        """

        loan_ids = Amortization.objects.filter(
            due_date__month=timezone.now().month
        ).values_list("loan", flat=True).distinct()
        loans = Loan.objects.filter(id__in=loan_ids)
        amount = loans.annotate(
            interest=Case(
                When(
                    source__capital_source__source=CapitalSource.SOURCES.savings,
                    then=F("amount") * (F("interest_rate") / 100)
                ),
                When(
                    ~Q(source__capital_source__source=CapitalSource.SOURCES.savings),
                    then=(
                        F("amount") * (F("interest_rate") / 100) -
                        F("source__amount") * (F("source__interest_rate") / 100)
                    )
                ),
            )
        ).aggregate(total=Sum("interest"))
        return math.floor(amount["total"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "active_loans": self.get_active_loans(),
            "current_month_earnings": self.get_earnings_for_current_month(),
        })
        return context
