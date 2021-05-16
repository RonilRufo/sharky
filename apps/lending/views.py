from dateutil.relativedelta import relativedelta

from django.db.models import Count, Q
from django.http import Http404
from django.http.response import JsonResponse
from django.utils import timezone
from django.views.generic import View

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
        graph_data = []
        for i in range(12):
            labels.append(loan_date.strftime("%b %Y"))

            loan_ids = Amortization.objects.filter(
                due_date__month=loan_date.month,
                due_date__year=loan_date.year
            ).values_list("loan", flat=True).distinct()
            graph_data.append(Loan.objects.filter(id__in=loan_ids).total_interest_earned())

            loan_date += relativedelta(months=1)

        return JsonResponse(
            {
                "labels": labels,
                "graph_data": graph_data,
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
