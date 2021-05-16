"""
URL patterns in lending app
"""
from django.urls import path

from .views import EarningsGraph, LoanSourcesGraph

app_name = "lending"
urlpatterns = [
    path("earnings-graph/", EarningsGraph.as_view(), name="earnings-graph"),
    path("loan-sources-graph/", LoanSourcesGraph.as_view(), name="loan-sources-graph"),
]
