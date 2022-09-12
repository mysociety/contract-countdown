from urllib.parse import unquote
from datetime import date, timedelta

from django.db.models import F
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView

from django_filters.views import FilterView

from procurement.models import Council, Tender
from procurement.filters import TenderFilter
from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)


class HomePageView(FilterView):
    paginate_by = 20
    context_object_name = "tenders"
    template_name = "procurement/home.html"
    filterset_class = TenderFilter

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .select_related("council")
            .prefetch_related("awards")
            .order_by("value")
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Contract Countdown"
        context["all_councils"] = Council.objects.all()

        today = date.today()
        months = (6, 12, 18, 24)
        for month in months:
            end = today + timedelta(days=30 * month)
            context["{}_months".format(month)] = end.isoformat()

        if context["filter"].form["awards__end_date"].value():
            context["filter_end_date"] = (
                context["filter"].form["awards__end_date"].value()[0]
            )

        if context["filter"].form["classification"].value():
            context["classifications"] = (
                context["filter"].form["classification"].value()
            )

        return context


class CouncilContractsView(FilterView):
    paginate_by = 20
    context_object_name = "tenders"
    filterset_class = TenderFilter
    template_name = "procurement/council_detail.html"

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .filter(state="complete")
            .select_related("council")
            .prefetch_related("awards")
            .order_by("value")
        )

        slug = self.kwargs.get("slug")
        if slug is not None:
            qs = qs.filter(council__slug=slug)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get("slug")
        council = get_object_or_404(Council, slug=slug)
        context["council"] = council

        return context


class ContractDetailView(DetailView):
    model = Tender
    context_object_name = "tender"
    template_name = "procurement/contract_detail.html"
    slug_field = "uuid"

    def get_object(self):
        slug = unquote(self.kwargs[self.slug_url_kwarg])
        obj = get_object_or_404(Tender, uuid=slug)
        return obj

class EmailAlertView(FilterView):
    paginate_by = 20
    context_object_name = "tenders"
    filterset_class = TenderFilter
    template_name = "procurement/emails.html"

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .select_related("council")
            .prefetch_related("awards")
            .order_by("value")
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if context["filter"].form["classification"].value():
            context["classifications"] = (
                context["filter"].form["classification"].value()
            )
        return context