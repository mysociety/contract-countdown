from urllib.parse import unquote
from datetime import date, timedelta

from django.db.models import F
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView

from django_filters.views import FilterView

from procurement.models import Council, Tender, TenderFilter
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


class CouncilContractsView(DetailView):

    model = Council
    context_object_name = "council"
    template_name = "procurement/council_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        council = context["council"]
        tenders = Tender.objects.filter(council=council, value__gt=0)[:100]

        context["tenders"] = tenders
        context["page_title"] = "{} Contracts".format(council.name)
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

class BaseLocationResultsView(TemplateView):
    def render_to_response(self, context):
        councils = context.get("councils")
        if councils and len(councils) == 1:
            return redirect(context["councils"][0])

        return super(BaseLocationResultsView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        postcode = self.request.GET.get("pc")
        lon = self.request.GET.get("lon")
        lat = self.request.GET.get("lat")
        mapit = MapIt()
        context["postcode"] = postcode
        context["all_councils"] = Council.objects.all()
        try:
            if lon and lat:
                gss_codes = mapit.wgs84_point_to_gss_codes(lon, lat)
            elif postcode:
                gss_codes = mapit.postcode_point_to_gss_codes(postcode)
            else:
                return context
            councils = Council.objects.filter(gss_code__in=gss_codes)
            context["councils"] = list(councils)
        except (
            NotFoundException,
            BadRequestException,
            InternalServerErrorException,
            ForbiddenException,
        ) as error:
            context["error"] = error

        return context


class LocationResultsView(BaseLocationResultsView):
    template_name = "procurement/location_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if context.get("postcode", "") != "":
            context["page_title"] = "{} – Find your council’s contracts".format(
                context["postcode"]
            )
        else:
            context["page_title"] = "Find your council’s contracts"

        return context
