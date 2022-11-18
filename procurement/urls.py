from django.contrib import admin
from django.urls import path, include
from django.conf import settings

import procurement.views as views

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("contract/<slug>/", views.ContractDetailView.as_view(), name="contract"),
    path("emails/", views.EmailAlertView.as_view(), name="emails"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("contact/<slug:council>/", views.ContactCouncilView.as_view(), name="contact_council"),
    path("contact/<slug:council>/<slug:representative>/", views.ContactRepresentativeView.as_view(), name="contact_representative"),
    path("contact/<slug:council>/<slug:representative>/preview/", views.ContactPreviewView.as_view(), name="preview"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
