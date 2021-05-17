from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, query
from django.http import Http404
from django.http.response import JsonResponse
from django.utils import timezone
from django.views.generic import View, ListView

from apps.lending.models import Amortization, CapitalSource, Loan


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

            loan_ids = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.principal_only),
                due_date__month=loan_date.month,
                due_date__year=loan_date.year,
                is_preterminated=False,
            ).values_list("loan", flat=True).distinct()
            interest_data.append(
                Loan.objects.filter(id__in=loan_ids).total_interest_earned()
            )

            principal_loan_ids = Amortization.objects.filter(
                ~Q(amort_type=Amortization.AMORTIZATION_TYPES.interest_only),
                loan__source__capital_source__source=CapitalSource.SOURCES.savings,
                due_date__month=loan_date.month,
                due_date__year=loan_date.year
            ).values_list("loan", flat=True).distinct()
            principal_data.append(
                Loan.objects.filter(
                    id__in=principal_loan_ids
                ).total_principal_receivables()
            )

            loan_date += relativedelta(months=1)

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
                filter=Q(source__capital_source__source=CapitalSource.SOURCES.savings)
            ),
            credit_card=Count(
                "pk",
                filter=Q(
                    source__capital_source__source=CapitalSource.SOURCES.credit_card
                )
            ),
            cash_loan=Count(
                "pk",
                filter=Q(source__capital_source__source=CapitalSource.SOURCES.loan)
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
        due_date__lte=timezone.now(),
        paid_date__isnull=True,
    )
    template_name = "lending/amortization/past_due.html"
    context_object_name = "amortizations"


class ActiveLoans(LoginRequiredMixin, ListView):
    """
    Displays list of active loans.
    """

    queryset = Loan.objects.filter(is_completed=False)
    template_name = "lending/loan/list.html"
    context_object_name = "loans"
