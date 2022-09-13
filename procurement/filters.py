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

    council = filters.ModelMultipleChoiceFilter(
        field_name="council__name",
        queryset=Council.objects.all().distinct("name"),
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

    class Meta:
        model = Tender
        fields = ["awards__end_date", "classification"]