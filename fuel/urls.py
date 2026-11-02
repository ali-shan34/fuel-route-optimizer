from django.urls import path

from fuel.views import FuelStationListAPIView, RouteAPIView


urlpatterns = [
    path(
        "stations/",
        FuelStationListAPIView.as_view(),
        name="fuel-station-list",
    ),
    path(
        "route/",
        RouteAPIView.as_view(),
        name="route-api",
    ),
]