import math
from typing import Any, Dict, Optional

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView

from apps.lending.models import Amortization, CapitalSource, Loan


class Dashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Displays the dashboard page.
    """

    template_name = "index.html"

    def test_func(self) -> Optional[bool]:
        return self.request.user.is_superuser

    def get_past_due_amortizations(self) -> int:
        """
        Returns the number of past due amortizations.
        """
        return Amortization.objects.filter(
            due_date__lte=timezone.now(), paid_date__isnull=True
        ).count()

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
        loan_ids = (
            Amortization.objects.filter(
                due_date__month=now.month,
                due_date__year=now.year,
                is_preterminated=False,
            )
            .values_list("loan", flat=True)
            .distinct()
        )
        return Loan.objects.filter(id__in=loan_ids).total_interest_earned()

    def get_total_principal_receivables(self) -> int:
        """
        Returns the total principal receivables for all active loans with source coming
        from a savings account.
        """
        loan_ids = (
            Amortization.objects.filter(paid_date__isnull=True)
            .values_list("loan", flat=True)
            .distinct()
        )
        loans = Loan.objects.filter(id__in=loan_ids)
        amount = loans.annotate(
            principal=Case(
                When(
                    source__capital_source__source=CapitalSource.SOURCES.savings,
                    payment_schedule=Loan.PAYMENT_SCHEDULES.monthly,
                    then=(
                        (F("amount") / F("term"))
                        * Count(
                            "amortizations",
                            filter=Q(amortizations__paid_date__isnull=True),
                        )
                    ),
                ),
                When(
                    source__capital_source__source=CapitalSource.SOURCES.savings,
                    payment_schedule=Loan.PAYMENT_SCHEDULES.bi_monthly,
                    then=(
                        (F("amount") / F("term"))
                        * (
                            Count(
                                "amortizations",
                                filter=Q(amortizations__paid_date__isnull=True),
                            )
                        )
                        / 2
                    ),
                ),
                default=Value(0),
                output_field=DecimalField(),
            )
        ).aggregate(total=Sum("principal"))
        return math.floor(amount["total"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_loans": self.get_active_loans(),
                "current_month_earnings": self.get_earnings_for_current_month(),
                "total_principal_receivables": self.get_total_principal_receivables(),
                "past_due_amortizations": self.get_past_due_amortizations(),
            }
        )
        return context


class Index(RedirectView):
    """
    Redirects to the corresponding pages when index page is accessed.
    """

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Returns the URL to redirect to.
        """
        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return reverse_lazy("dashboard")
        elif user.is_authenticated and user.is_borrower:
            return reverse_lazy("lending:loans-active")
        else:
            return reverse_lazy("accounts:login")
