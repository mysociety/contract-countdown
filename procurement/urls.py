from django.contrib import admin
from django.urls import path

import procurement.views as views

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("admin/", admin.site.urls),
]
