from datetime import date

from django.db import models
from django.utils.text import slugify

import django_filters as filters


class Council(models.Model):
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    authority_code = models.CharField(max_length=4, unique=True)
    gss_code = models.CharField(max_length=9, blank=True, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return "%s" % self.name

    @classmethod
    def slugify_name(cls, name):
        return slugify(name, allow_unicode=True)

    def get_absolute_url(self):
        return "/council/%s/" % self.slug


class Supplier(models.Model):
    name = models.CharField(max_length=200)


class Tender(models.Model):
    uuid = models.CharField(max_length=100)
    title = models.TextField()
    description = models.TextField()
    state = models.CharField(max_length=50)
    value = models.FloatField(default=0)

    council = models.ForeignKey(Council, on_delete=models.CASCADE)

    """
    created
    due
    awarded_on
    awarded_to
    starts
    ends
    classification
    value

    ????
    emissions scope
    emissions amount
    """


class TenderFilter(filters.FilterSet):
    awards__end_date = filters.DateFromToRangeFilter()

    sort=filters.OrderingFilter(
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

    class Meta:
        model = Tender
        fields = ["awards__end_date"]


class Award(models.Model):
    uuid = models.CharField(max_length=100)
    value = models.FloatField(default=0, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    duration = models.IntegerField(
        blank=True, null=True, help_text="contract length in days"
    )

    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="awards")

    def contract_length(self):
        if self.end_date is None or self.start_date is None:
            return None

        return self.end_date - self.start_date

    def contract_length_desc(self):
        timedelta = self.contract_length()
        if timedelta is None:
            return "contract length unknown"

        if timedelta.days > 30:
            return "{} month contract".format(int(timedelta.days / 30))
        else:
            return "{} day contract".format(timedelta.days)

    def contract_percent_remaining(self):
        if self.start_date is None or self.end_date is None:
            return 100

        if self.contract_length().days == 0:
            return 0

        time_since_start = date.today() - self.start_date
        return time_since_start.days / self.contract_length().days * 100

    def contract_time_remaining(self):
        if self.end_date is None:
            return None

        return self.end_date - date.today()

    def contract_time_remaining_desc(self):
        timedelta = self.contract_time_remaining()
        if timedelta is None:
            if self.end_date is not None:
                return "Contract ends: {}".format(self.end_date.ymd)
            else:
                return "Contract end unknown"

        if timedelta.days > 30:
            return "{} months left".format(int(timedelta.days / 30))
        else:
            return "{} days left".format(timedelta.days)
