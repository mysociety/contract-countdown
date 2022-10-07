from django.contrib import admin
from django.urls import path, include
from django.conf import settings

import procurement.views as views

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("council/<slug:slug>/", views.CouncilContractsView.as_view(), name="council"),
    path("contract/<slug>/", views.ContractDetailView.as_view(), name="contract"),
    path("emails/", views.EmailAlertView.as_view(), name="emails"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
