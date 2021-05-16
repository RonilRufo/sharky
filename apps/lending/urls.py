"""
URL patterns in lending app
"""
from django.urls import path

from .views import EarningsGraph

app_name = "lending"
urlpatterns = [
    path("earnings-graph/", EarningsGraph.as_view(), name="earnings-graph"),
]
