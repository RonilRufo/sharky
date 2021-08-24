from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q, Sum
from django.http import Http404
from django.http.response import JsonResponse
from django.utils import timezone
from django.views.generic import ListView, View

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
                due_date__month=paid_date.month,
                due_date__year=paid_date.year,
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
                filter=Q(source__capital_source__source=CapitalSource.SOURCES.savings),
            ),
            credit_card=Count(
                "pk",
                filter=Q(
                    source__capital_source__source=CapitalSource.SOURCES.credit_card
                ),
            ),
            cash_loan=Count(
                "pk",
                filter=Q(source__capital_source__source=CapitalSource.SOURCES.loan),
            ),
        )
        graph_data = [value for key, value in data.items()]

        return JsonResponse(
            {
                "labels": labels,
                "graph_data": graph_data,
            }
        )


class PastDueList(LoginRequiredMixin, ListView):
    """
    Displays a list of amortization that are past due.
    """

    queryset = Amortization.objects.filter(
        due_date__lte=timezone.now().date(),
        paid_date__isnull=True,
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


class ActiveLoans(LoginRequiredMixin, ListView):
    """
    Displays list of active loans.
    """

    queryset = Loan.objects.filter(is_completed=False)
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
