import math
from decimal import Decimal
from typing import Any, Dict, List, Union

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, QuerySet, Sum
from django.http import Http404
from django.http.response import JsonResponse
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from apps.accounts.models import EmailUser
from apps.lending.models import Amortization, CapitalSource, Loan, LoanSource


class EarningsGraph(View):
    """
    Returns data for plotting the earnings graph in dashboard page.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request to this view. Only accepts aJax requests.
        """
        is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
        if not is_ajax:
            raise Http404()

        now = timezone.now()
        loan_date = now - relativedelta(months=5)
        labels = []
        interest_data = []
        principal_data = []
        for i in range(12):
            labels.append(loan_date.strftime("%b %Y"))

            amortizations = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.principal_only),
                due_date__month=loan_date.month,
                due_date__year=loan_date.year,
                is_preterminated=False,
            ).aggregate(total_gained=Sum("amount_gained"))

            interest_data.append(amortizations["total_gained"])

            principal_amortization = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.interest_only),
                due_date__month=loan_date.month,
                due_date__year=loan_date.year,
            ).distinct()

            receivable = (
                LoanSource.objects.filter(
                    loan__amortizations__in=principal_amortization,
                    capital_source__source=CapitalSource.SOURCES.savings,
                    capital_source__provider__isnull=True,
                )
                .distinct()
                .annotate(receivables=F("amount") / F("loan__term"))
                .aggregate(total=Sum("receivables"))
            )

            principal_data.append(receivable["total"])

            loan_date += relativedelta(months=1)

        return JsonResponse(
            {
                "labels": labels,
                "interest_data": interest_data,
                "principal_data": principal_data,
            }
        )


class MoneyReturnedGraph(View):
    """
    Returns data for plotting the money returned graph in dashboard page. This graph
    displays the amount returned(interest and principal) based on the date paid on the
    amortization.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request to this view. Only accepts aJax requests.
        """
        is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
        if not is_ajax:
            raise Http404()

        now = timezone.now()
        paid_date = now - relativedelta(months=11)
        labels = []
        interest_data = []
        principal_data = []
        for i in range(12):
            labels.append(paid_date.strftime("%b %Y"))

            amortizations = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.principal_only),
                paid_date__month=paid_date.month,
                paid_date__year=paid_date.year,
                is_preterminated=False,
            ).aggregate(total_gained=Sum("amount_gained"))

            interest_data.append(amortizations["total_gained"])

            principal_amortization = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.interest_only),
                paid_date__month=paid_date.month,
                paid_date__year=paid_date.year,
            ).distinct()

            receivable = (
                LoanSource.objects.filter(
                    loan__amortizations__in=principal_amortization,
                    capital_source__source=CapitalSource.SOURCES.savings,
                    capital_source__provider__isnull=True,
                )
                .distinct()
                .annotate(receivables=F("amount") / F("loan__term"))
                .aggregate(total=Sum("receivables"))
            )

            principal_data.append(receivable["total"])

            paid_date += relativedelta(months=1)

        return JsonResponse(
            {
                "labels": labels,
                "interest_data": interest_data,
                "principal_data": principal_data,
            }
        )


class LoanSourcesGraph(View):
    """
    Returns data for plotting the loan sources graph in dashboard page.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request to this view. Only accepts aJax requests.
        """
        is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
        if not is_ajax:
            raise Http404()

        labels = [source[1] for source in CapitalSource.SOURCES]
        data = Loan.objects.aggregate(
            savings=Count(
                "pk",
                filter=Q(sources__capital_source__source=CapitalSource.SOURCES.savings),
            ),
            credit_card=Count(
                "pk",
                filter=Q(
                    sources__capital_source__source=CapitalSource.SOURCES.credit_card
                ),
            ),
            cash_loan=Count(
                "pk",
                filter=Q(sources__capital_source__source=CapitalSource.SOURCES.loan),
            ),
        )
        graph_data = [value for key, value in data.items()]

        return JsonResponse(
            {
                "labels": labels,
                "graph_data": graph_data,
            }
        )


class ShowAmortizationContextMixin:
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update({"show_amortization_menu": True})
        return data


class PastDueList(LoginRequiredMixin, ShowAmortizationContextMixin, ListView):
    """
    Displays a list of amortization that are past due.
    """

    queryset = (
        Amortization.objects.select_related(
            "loan",
            "loan__borrower",
        )
        .prefetch_related(
            "loan__sources",
            "loan__sources__capital_source",
        )
        .filter(
            due_date__lte=timezone.now().date(),
            paid_date__isnull=True,
        )
        .exclude(
            loan__borrower__is_borrower_active=False,
        )
    )
    template_name = "lending/amortization/past_due.html"
    context_object_name = "amortizations"

    def get_queryset(self, *args, **kwargs):
        """
        Custom queryset for past due list.
        """
        queryset = super().get_queryset(*args, **kwargs)
        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(loan__borrower=self.request.user)


class UpcomingDueList(LoginRequiredMixin, ShowAmortizationContextMixin, ListView):
    """
    Displays a list of amortization that are due in the next 7 days.
    """

    queryset = (
        Amortization.objects.select_related(
            "loan",
            "loan__borrower",
        )
        .prefetch_related(
            "loan__sources",
            "loan__sources__capital_source",
        )
        .filter(
            due_date__range=(
                timezone.now().date() + relativedelta(days=1),
                timezone.now().date() + relativedelta(days=7),
            ),
            paid_date__isnull=True,
        )
        .exclude(
            loan__borrower__is_borrower_active=False,
        )
    )
    template_name = "lending/amortization/upcoming_due.html"
    context_object_name = "amortizations"

    def get_queryset(self, *args, **kwargs):
        """
        Custom queryset for upcoming due list.
        """
        queryset = super().get_queryset(*args, **kwargs)
        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(loan__borrower=self.request.user)


class ActiveLoans(LoginRequiredMixin, ListView):
    """
    Displays list of active loans.
    """

    queryset = (
        Loan.objects.select_related(
            "borrower",
        )
        .prefetch_related(
            "sources",
            "sources__capital_source",
        )
        .filter(
            is_completed=False,
        )
        .exclude(
            borrower__is_borrower_active=False,
        )
    )
    template_name = "lending/loan/list.html"
    context_object_name = "loans"

    def get_queryset(self, *args, **kwargs):
        """
        Custom queryset for active loans.
        """
        queryset = super().get_queryset(*args, **kwargs)
        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(borrower=self.request.user)


class BorrowerDetail(LoginRequiredMixin, DetailView):
    """
    Retrieves a single borrower(:model:`accounts.EmailUser`) object.
    """

    queryset = EmailUser.objects.filter(is_borrower=True)
    context_object_name = "borrower"
    template_name = "lending/borrower/detail.html"

    def get_object(self) -> EmailUser:
        obj = super().get_object()
        if self.request.user.is_superuser or self.request.user == obj:
            return obj

        raise PermissionDenied()

    def get_past_due_amortizations(self) -> Union[QuerySet, List[Amortization]]:
        """
        Returns the past due amortizations of the selected borrower.
        """
        obj = self.get_object()
        return Amortization.objects.filter(
            loan__borrower=obj,
            due_date__lte=timezone.now().date(),
            paid_date__isnull=True,
        )

    def get_total_past_due_payables(self) -> Union[int, Decimal]:
        """
        Returns the total payable of the borrower from loans which are already past due.
        """
        amortizations = self.get_past_due_amortizations().aggregate(
            total_payable=Sum("amount_due")
        )
        return math.ceil(amortizations["total_payable"] or 0)

    def get_total_principal_receivables(self) -> Union[int, Decimal]:
        """
        Returns the total principal receivables of the borrower from loans which are
        already past due.
        """
        amortizations = self.get_past_due_amortizations()
        receivable = (
            LoanSource.objects.filter(
                loan__amortizations__in=amortizations,
                capital_source__source=CapitalSource.SOURCES.savings,
                capital_source__provider__isnull=True,
            )
            .distinct()
            .annotate(receivables=F("amount") / F("loan__term"))
            .aggregate(total=Sum("receivables"))
        )
        return math.ceil(receivable["total"] or 0)

    def get_total_past_due_amount_earned(self) -> Union[int, Decimal]:
        """
        Returns the total amount earned based on the past due amortizations.
        """
        amortizations = self.get_past_due_amortizations().aggregate(
            total_earned=Sum("amount_gained")
        )
        return math.ceil(amortizations["total_earned"] or 0)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "total_amount_earned": self.get_total_past_due_amount_earned(),
                "total_payable": self.get_total_past_due_payables(),
                "total_principal": self.get_total_principal_receivables(),
                "active_loans": self.get_object().loans.filter(is_completed=False),
                "amortizations": self.get_past_due_amortizations(),
            }
        )
        return context
