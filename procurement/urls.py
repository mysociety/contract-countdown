from django.contrib import admin
from django.urls import path, include
from django.conf import settings

import procurement.views as views

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("council/<slug:slug>/", views.CouncilContractsView.as_view(), name="council"),
    path("location/", views.LocationResultsView.as_view(), name="location_results"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
