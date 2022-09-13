from urllib.parse import quote
from datetime import date

from django.db import models
from django.utils.text import slugify


class Council(models.Model):
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    authority_code = models.CharField(max_length=5, unique=True)
    gss_code = models.CharField(max_length=9, blank=True)
    nation = models.CharField(max_length=16)
    region = models.CharField(max_length=24)

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
    published = models.DateField(null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

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

    def uuid_url_safe(self):
        return quote(self.uuid, safe="")


class Classification(models.Model):
    description = models.CharField(max_length=500)
    classification_scheme = models.CharField(max_length=200)
    group = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return str(self.group)


class TenderClassification(models.Model):
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, related_name="tenderclassification"
    )
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)


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

    def contract_current(self):
        today = date.today()
        return self.contract_started() and not self.contract_ended()

    def contract_started(self):
        today = date.today()
        return today > self.start_date

    def contract_ended(self):
        today = date.today()
        return today > self.end_date

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

    def contract_percent_complete(self):
        if self.start_date is None or self.end_date is None:
            return 100

        if self.contract_length().days == 0 or not self.contract_started():
            return 0

        if self.contract_ended():
            return 100

        time_since_start = date.today() - self.start_date
        return time_since_start.days / self.contract_length().days * 100

    def contract_time_remaining(self):
        if self.end_date is None:
            return None

        return self.end_date - date.today()

    def contract_time_remaining_desc(self):
        timedelta = self.contract_time_remaining()
        if not self.contract_started():
            return "Contract starts: {}".format(self.start_date.isoformat())
        elif self.contract_ended():
            return "Contract ends: {}".format(self.end_date.isoformat())

        if timedelta is None:
            if self.end_date is not None:
                return "Contract ends: {}".format(self.end_date.ymd)
            else:
                return "Contract end unknown"

        if timedelta.days > 30:
            return "{} months left".format(int(timedelta.days / 30))
        else:
            return "{} days left".format(timedelta.days)
