import math
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, Count, F, Q, Sum, Value, When, DecimalField
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
        now = timezone.now()
        loan_ids = Amortization.objects.filter(
            due_date__month=now.month,
            due_date__year=now.year
        ).values_list("loan", flat=True).distinct()
        return Loan.objects.filter(id__in=loan_ids).total_interest_earned()

    def get_total_principal_receivables(self) -> int:
        """
        Returns the total principal receivables for all active loans with source coming
        from a savings account.
        """
        loan_ids = Amortization.objects.filter(
            paid_date__isnull=True
        ).values_list("loan", flat=True).distinct()
        loans = Loan.objects.filter(id__in=loan_ids)
        amount = loans.annotate(
            principal=Case(
                When(
                    source__capital_source__source=CapitalSource.SOURCES.savings,
                    payment_schedule=Loan.PAYMENT_SCHEDULES.monthly,
                    then=(
                        (F("amount") / F("term")) *
                        Count(
                            "amortizations",
                            filter=Q(amortizations__paid_date__isnull=True)
                        )
                    ),
                ),
                When(
                    source__capital_source__source=CapitalSource.SOURCES.savings,
                    payment_schedule=Loan.PAYMENT_SCHEDULES.bi_monthly,
                    then=(
                        (F("amount") / F("term")) *
                        (
                            Count(
                                "amortizations",
                                filter=Q(amortizations__paid_date__isnull=True)
                            ) / 2
                        )
                    )
                ),
                default=Value(0),
                output_field=DecimalField()
            )
        ).aggregate(total=Sum("principal"))
        return math.floor(amount["total"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "active_loans": self.get_active_loans(),
            "current_month_earnings": self.get_earnings_for_current_month(),
            "total_principal_receivables": self.get_total_principal_receivables(),
        })
        return context
