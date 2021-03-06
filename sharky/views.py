import math
from typing import Any, Dict, Optional

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView

from apps.lending.models import Amortization, CapitalSource, Loan, LoanSource


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
        return (
            Amortization.objects.filter(
                due_date__lte=timezone.now(),
                paid_date__isnull=True,
            )
            .exclude(
                loan__borrower__is_borrower_active=False,
            )
            .count()
        )

    def get_active_loans(self) -> int:
        """
        Returns the number of active loans.
        """
        return (
            Loan.objects.filter(
                is_completed=False,
            )
            .exclude(
                borrower__is_borrower_active=False,
            )
            .count()
        )

    def get_earnings_for_current_month(self) -> int:
        """
        Returns the earnings from all loans for the current month.
        """
        now = timezone.now()
        amortizations = (
            Amortization.objects.filter(
                due_date__month=now.month,
                due_date__year=now.year,
                is_preterminated=False,
            )
            .exclude(
                loan__borrower__is_borrower_active=False,
            )
            .aggregate(
                total_gained=Sum("amount_gained"),
            )
        )
        return amortizations["total_gained"] or 0

    def get_total_principal_receivables(self) -> int:
        """
        Returns the total principal receivables for all active loans with source coming
        from a savings account.
        """

        sources = (
            LoanSource.objects.filter(
                capital_source__source=CapitalSource.SOURCES.savings,
                capital_source__provider__isnull=True,
            )
            .exclude(
                loan__borrower__is_borrower_active=False,
            )
            .annotate(
                receivables=Case(
                    When(
                        loan__payment_schedule=Loan.PAYMENT_SCHEDULES.monthly,
                        then=(
                            F("amount")
                            / F("loan__term")
                            * Count(
                                "loan__amortizations",
                                filter=Q(loan__amortizations__paid_date__isnull=True),
                            )
                        ),
                    ),
                    When(
                        loan__payment_schedule=Loan.PAYMENT_SCHEDULES.bi_monthly,
                        then=(
                            (F("amount") / F("loan__term"))
                            * (
                                Count(
                                    "loan__amortizations",
                                    filter=Q(
                                        loan__amortizations__paid_date__isnull=True
                                    ),
                                )
                            )
                            / 2
                        ),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
            .aggregate(total=Sum("receivables"))
        )

        return math.floor(sources["total"] or 0)

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
            return reverse_lazy("lending:borrowers-detail", args=(user.pk,))
        else:
            return reverse_lazy("accounts:login")
