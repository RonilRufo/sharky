"""
URL patterns in lending app
"""
from django.urls import path

from .views import (
    ActiveLoans,
    BorrowerDetail,
    EarningsGraph,
    LoanSourcesGraph,
    MoneyReturnedGraph,
    PastDueList,
)

app_name = "lending"
urlpatterns = [
    path("earnings-graph/", EarningsGraph.as_view(), name="earnings-graph"),
    path("loan-sources-graph/", LoanSourcesGraph.as_view(), name="loan-sources-graph"),
    path(
        "money-returned-graph/",
        MoneyReturnedGraph.as_view(),
        name="money-returned-graph",
    ),
    path("amortization/past-due/", PastDueList.as_view(), name="past-due-list"),
    path("loans/active/", ActiveLoans.as_view(), name="loans-active"),
    path("borrowers/<uuid:pk>/", BorrowerDetail.as_view(), name="borrowers-detail"),
]
