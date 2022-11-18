import datetime

import django_filters as filters
import django.forms as forms

from procurement.models import Classification, Council, Tender
from procurement.forms import PostcodeForm

NOTIFICATION_MONTHS = [datetime.timedelta(days=x * 30) for x in [3, 6, 12, 18]]


class BaseTenderFilter(filters.FilterSet):
    classification = filters.ModelMultipleChoiceFilter(
        field_name="tenderclassification__classification__group",
        queryset=Classification.objects.all().distinct("group").exclude(group=None),
        to_field_name="group",
        widget=forms.CheckboxSelectMultiple(),
    )

    awards__end_date = filters.DateFromToRangeFilter()

    class Meta:
        model = Tender
        fields = ["classification"]


class HomePageTenderFilter(BaseTenderFilter):
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
    pc = filters.CharFilter(
        field_name="council__gss_code",
        lookup_expr="in",
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "name": "pc",
                "id": "council-search",
                "class": "form-control",
            }
        ),
    )
    class Meta:
        form = PostcodeForm


class EmailAlertPageTenderFilter(BaseTenderFilter):
    source = filters.CharFilter(
        method="filter_source",
        widget=forms.RadioSelect(
            choices=(
                ("all", "All UK councils"),
                ("region", "Councils in a region..."),
                ("council", "My council..."),
            )
        ),
    )

    notification_frequency = filters.ChoiceFilter(
        field_name="published",
        method="filter_notification_frequency",
        choices=((1, "Daily"), (7, "Weekly"), (30, "Monthly")),
        widget=forms.Select(attrs={"class": "form-select", "id": "frequency"}),
    )

    def filter_source(self, queryset, name, value):
        if value == "Councils in a region...":
            region = self.request.GET.get("region")
            countries = [x[0] for x in Council.COUNTRY_CHOICES]
            # TODO: Wales + Scotland
            if region in countries:
                return queryset.filter(council__nation=region)
            else:
                return queryset.filter(council__region=region)
        elif value == "My council...":
            council = self.request.GET.get("council_exact")
            return queryset.filter(council__name=council)
        else:
            return queryset

    def filter_notification_frequency(self, queryset, name, value):
        today = datetime.date.today()
        days_in_timeframe = [
            today - datetime.timedelta(days=i) for i in range(int(value) + 1)
        ]
        possible_end_dates = []
        for day in days_in_timeframe:
            for future_day in NOTIFICATION_MONTHS:
                possible_end_dates.append(day + future_day)
        return queryset.filter(end_date__in=possible_end_dates)
