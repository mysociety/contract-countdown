from urllib.parse import unquote
from datetime import date, timedelta

from django.db.models import F
from django.utils.http import urlencode
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView, FormView

from django_filters.views import FilterView

from procurement.models import ClimateRepresentative, Council, Tender
from procurement.filters import (
    EmailAlertPageTenderFilter,
    HomePageTenderFilter,
)
from procurement.forms import ContactPostcodeForm, ContactRepresentativeForm
from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)


def check_council_and_representative_match(view_class, context):
    context["council"] = get_object_or_404(Council, slug=view_class.kwargs["council"])
    representative = get_object_or_404(
        ClimateRepresentative, slug=view_class.kwargs["representative"]
    )
    if representative.council == context["council"]:
        context["representative"] = representative
    else:
        raise Http404("Representative and council don't match.")
    if view_class.request.GET.get("contract"):
        context["contract"] = Tender.objects.get(
            uuid=view_class.request.GET.get("contract")
        )
    return context


class HomePageView(FilterView):
    paginate_by = 20
    context_object_name = "tenders"
    template_name = "procurement/home.html"
    filterset_class = HomePageTenderFilter

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .filter(start_date__lte=date.today())
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
    filterset_class = HomePageTenderFilter
    template_name = "procurement/council_detail.html"

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .filter(start_date__lte=date.today())
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
        context["page_title"] = "{} | Contract Countdown".format(council.name)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "{} | Contract Countdown".format(self.get_object().title)

        return context


class EmailAlertView(FilterView):
    paginate_by = 20
    context_object_name = "tenders"
    filterset_class = EmailAlertPageTenderFilter
    template_name = "procurement/emails.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Email alerts | Contract Countdown"
        context["all_councils"] = Council.objects.all()
        if self.request.GET.get("source"):
            context["council_choice"] = self.request.GET.get("source")

        if context["filter"].form["classification"].value():
            context["classifications"] = (
                context["filter"].form["classification"].value()
            )

        if self.request.GET.get("region"):
            context["region_choice"] = self.request.GET.get("region")

        if self.request.GET.get("council_exact"):
            council = self.request.GET.get("council_exact")
            if not Council.objects.filter(name__iexact=council.lower()).exists():
                context["council_exact_error"] = "Invalid postcode or council"

        return context

    def get_queryset(self):
        qs = (
            Tender.objects.all()
            .filter(start_date__lte=date.today())
            .select_related("council")
            .prefetch_related("awards")
            .order_by("value")
        )

        return qs


class ContactView(FormView):
    template_name = "procurement/contact.html"
    form_class = ContactPostcodeForm

    def form_valid(self, form):
        council = Council.objects.filter(gss_code__in=form.cleaned_data["pc"])[0]
        return redirect("/contact/" + council.slug + "/")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "Contact a councillor | Contract Countdown"

        return context


class ContactCouncilView(TemplateView):
    template_name = "procurement/contact_council.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        council = get_object_or_404(Council, slug=self.kwargs["council"])

        if self.request.GET.get("contract"):
            context["contract"] = self.request.GET.get("contract")

        context["council"] = council
        context["officers"] = ClimateRepresentative.objects.filter(
            council=council
        ).filter(representative_type="officer")
        context["councillors"] = ClimateRepresentative.objects.filter(
            council=council
        ).filter(representative_type="councillor")

        context["page_title"] = "Contacts at {} | Contract Countdown".format(council.name)

        return context


class ContactRepresentativeView(FormView):
    template_name = "procurement/contact_representative.html"
    form_class = ContactRepresentativeForm

    def form_valid(self, form):
        self.request.session[
            "representative_form_" + self.kwargs["representative"]
        ] = form.data
        if self.request.GET.get("contract"):
            return redirect(
                "preview/?{query}".format(
                    query=urlencode({"contract": self.request.GET.get("contract")})
                )
            )
        else:
            return redirect("preview/")

    def get_initial(self):
        initial = super().get_initial()
        if (
            "representative_form_" + self.kwargs["representative"]
            in self.request.session
        ):
            initial.update(
                self.request.session.pop(
                    "representative_form_" + self.kwargs["representative"]
                )
            )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_object_or_404(Council, slug=self.kwargs["council"])
        context = check_council_and_representative_match(self, context)

        context["page_title"] = "Contact {} | Contract Countdown".format(context["representative"].full_name)

        return context


class ContactPreviewView(TemplateView):
    template_name = "procurement/contact_preview.html"
    # TODO: When implementing functionality for the submit button in this view,
    # be sure to also self.request.session.pop("representative_form_" + self.kwargs["representative"])
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = check_council_and_representative_match(self, context)
        if (
            "representative_form_" + self.kwargs["representative"]
            in self.request.session
        ):
            form = self.request.session[
                "representative_form_" + self.kwargs["representative"]
            ]
        else:
            raise Http404("No form data found.")
        context["message"] = form["message"]

        context["page_title"] = "Preview message to {} | Contract Countdown".format(context["representative"].full_name)

        return context
