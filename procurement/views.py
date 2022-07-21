from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView, DetailView

from procurement.models import Council, Tender
from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)

class HomePageView(ListView):
    paginate_by = 20
    context_object_name = "tenders"
    template_name = "procurement/home.html"

    def get_queryset(self):
        return Tender.objects.filter(value__gt=0)[:100]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Contract Countdown"
        return context


class CouncilContractsView(DetailView):

    model = Council
    context_object_name = "council"
    template_name = "procurement/council_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        council = context["council"]
        tenders = Tender.objects.filter(council=council,value__gt=0)[:100]

        context["tenders"] = tenders
        context["page_title"] = "{} Contracts".format(council.name)
        return context


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
                print(postcode)
                gss_codes = mapit.postcode_point_to_gss_codes(postcode)
            else:
                return context
            print(gss_codes)
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
