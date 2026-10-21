"""URLs da app de utilizadores."""

from django.urls import path

from .views import EuView

urlpatterns = [
    path("eu/", EuView.as_view(), name="eu"),
]
