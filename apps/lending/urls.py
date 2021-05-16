"""
URL patterns in lending app
"""
from django.urls import path

from .views import EarningsGraph, LoanSourcesGraph, PastDueList

app_name = "lending"
urlpatterns = [
    path("earnings-graph/", EarningsGraph.as_view(), name="earnings-graph"),
    path("loan-sources-graph/", LoanSourcesGraph.as_view(), name="loan-sources-graph"),
    path("amortization/past-due/", PastDueList.as_view(), name="past-due-list"),
]
