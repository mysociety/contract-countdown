from django.contrib import admin
from django.urls import path

import procurement.views as views

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("council/<slug:slug>/", views.CouncilContractsView.as_view(), name="council"),
    path("location/", views.LocationResultsView.as_view(), name="location_results"),
    path("admin/", admin.site.urls),
]
