import datetime

import django_filters as filters
import django.forms as forms

from procurement.mapit import (
    MapIt,
    NotFoundException,
    BadRequestException,
    InternalServerErrorException,
    ForbiddenException,
)
from procurement.models import Classification, Council, Tender

class TenderFilter(filters.FilterSet):
    awards__end_date = filters.DateFromToRangeFilter()
    classification = filters.ModelMultipleChoiceFilter(
        field_name="tenderclassification__classification__group",
        queryset=Classification.objects.all().distinct("group"),
        to_field_name="group",
        widget=forms.CheckboxSelectMultiple()
    )

    pc = filters.CharFilter(
        field_name="council__gss_code",
        method="filter_postcode",
    )

    council_exact = filters.ModelChoiceFilter(
        field_name="council__name",
        queryset=Council.objects.all().distinct("name"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "id": "search"
        })
    )

    region = filters.ChoiceFilter(
        choices=(("Regions of the UK", (Council.COUNTRY_CHOICES)), ("Regions of England", (Council.REGION_CHOICES))),
        method="filter_region",
        widget=forms.Select(attrs={"class":"form-select",
                                    "id": "region"})
    )

    state = filters.AllValuesFilter()

    sort = filters.OrderingFilter(
        label="Sort by",
        fields=(
            ("value", "value"),
            ("awards__duration", "contract_length"),
            ("awards__end_date", "time_remaining"),
        ),
        field_labels={
            "value": "Total Cost",
            "contract_length": "Contact Length",
            "time_remaining": "Contact Remaining",
        },
    )

    notification_frequency = filters.ChoiceFilter(
        field_name="published",
        method="filter_notification_frequency",
        choices=((1, "Daily"), (7, "Weekly"), (30, "Monthly")),
        widget=forms.Select(attrs={"class":"form-select",
                                    "id": "frequency"})
    )

    def filter_postcode(self, queryset, name, value):
        mapit = MapIt()

        gss_codes = None
        try:
            gss_codes = mapit.postcode_point_to_gss_codes(value)
        except (
            NotFoundException,
            BadRequestException,
            InternalServerErrorException,
            ForbiddenException,
        ) as error:
            pass

        if gss_codes is not None:
            return queryset.filter(**{"council__gss_code__in": gss_codes})

        return queryset

    def filter_region(self, queryset, name, value):
        countries = [x[0] for x in Council.COUNTRY_CHOICES]
        # TODO: Wales + Scotland
        if value in countries:
            print(queryset.filter(council__nation=value))
            return queryset.filter(council__nation=value)
        else:
            return queryset.filter(**{"council__region": value})

    def filter_notification_frequency(self, queryset, name, value):
        today = datetime.date.today()
        difference = datetime.timedelta(days=int(value))
        new_value = today - difference
        return queryset.filter(**{"published__gte": new_value})
    class Meta:
        model = Tender
        fields = ["awards__end_date", "classification"]