from django.test import TestCase

import datetime as dt

from procurement.models import Council, Classification, Tender, TenderClassification
from procurement.filters import TenderFilter

class TestEmailAlerts(TestCase):
    def setUp(self):
        now = dt.datetime.now()
        Council.objects.create(
            created_at=dt.datetime.now(),
            updated_at=dt.datetime.now(),
            name="Ceredigion County Council",
            slug="ceredigion",
            authority_code="CGN",
            gss_code="W06000008",
            nation="Wales",
            region="Wales"
            )
        Council.objects.create(
            created_at=dt.datetime.now(),
            updated_at=dt.datetime.now(),
            name="Aberdeenshire Council",
            slug="aberdeenshire",
            authority_code="ABD",
            gss_code="S12000034",
            nation="Scotland",
            region="Scotland"
            )
        Council.objects.create(
            created_at=dt.datetime.now(),
            updated_at=dt.datetime.now(),
            name="Bristol City Council",
            slug="bristol",
            authority_code="BST",
            gss_code="E06000023",
            nation="England",
            region="South West"
            )
        Council.objects.create(
            created_at=dt.datetime.now(),
            updated_at=dt.datetime.now(),
            name="Shropshire Council",
            slug="shropshire",
            authority_code="SHR",
            gss_code="E06000051",
            nation="England",
            region="West Midlands"
            )
        
        Tender.objects.create(
            uuid="ABC1",
            title="Test Tender 1",
            description="This is a test tender!",
            state="This is a test state",
            value=10000,
            published=now-dt.timedelta(days=1),
            start_date=dt.datetime(year=2022, month=12, day=1),
            end_date=dt.datetime(year=2022, month=12, day=31),
            council=Council.objects.get(name="Shropshire Council")
        )

        Tender.objects.create(
            uuid="ABC2",
            title="Test Tender 2",
            description="This is a test tender!",
            state="This is a test state",
            value=10000,
            published=now-dt.timedelta(hours=4),
            start_date=dt.datetime(year=2022, month=12, day=1),
            end_date=dt.datetime(year=2022, month=12, day=31),
            council=Council.objects.get(name="Shropshire Council")
        )

        Tender.objects.create(
            uuid="ABC3",
            title="Test Tender 3",
            description="This is a test tender!",
            state="This is a test state",
            value=10000,
            published=now-dt.timedelta(days=5),
            start_date=dt.datetime(year=2022, month=12, day=1),
            end_date=dt.datetime(year=2022, month=12, day=31),
            council=Council.objects.get(name="Ceredigion County Council")
        )

        Tender.objects.create(
            uuid="ABC4",
            title="Test Tender 4",
            description="This is a test tender!",
            state="This is a test state",
            value=10000,
            published=now-dt.timedelta(days=12),
            start_date=dt.datetime(year=2022, month=12, day=1),
            end_date=dt.datetime(year=2022, month=12, day=31),
            council=Council.objects.get(name="Aberdeenshire Council")
        )

        Tender.objects.create(
            uuid="ABC5",
            title="Test Tender 5",
            description="This is a test tender!",
            state="This is a test state",
            value=10000,
            published=now-dt.timedelta(days=14),
            start_date=dt.datetime(year=2022, month=12, day=1),
            end_date=dt.datetime(year=2022, month=12, day=31),
            council=Council.objects.get(name="Bristol City Council")
        )

        Classification.objects.create(
            description="Test classification!",
            classification_scheme="Test scheme!",
            group="A"
        )

        Classification.objects.create(
            description="Test classification!",
            classification_scheme="Test scheme!",
            group="B"
        )

        Classification.objects.create(
            description="Test classification!",
            classification_scheme="Test scheme!",
            group="C"
        )

        TenderClassification.objects.create(
            tender=Tender.objects.get(uuid="ABC5"),
            classification=Classification.objects.get(group="C")
        )

        TenderClassification.objects.create(
            tender=Tender.objects.get(uuid="ABC4"),
            classification=Classification.objects.get(group="C")
        )

        TenderClassification.objects.create(
            tender=Tender.objects.get(uuid="ABC3"),
            classification=Classification.objects.get(group="B")
        )

        TenderClassification.objects.create(
            tender=Tender.objects.get(uuid="ABC2"),
            classification=Classification.objects.get(group="A")
        )

        TenderClassification.objects.create(
            tender=Tender.objects.get(uuid="ABC1"),
            classification=Classification.objects.get(group="B")
        )


    def test_regions_filter_with_country(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={"region": "England"}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2", "ABC5"])), ordered=False)

    def test_countries_filter_with_region(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={"region": "West Midlands"}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2"])), ordered=False)

    def test_daily_alerts(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'notification_frequency': 1}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2"])), ordered=False)


    def test_weeky_alerts(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'notification_frequency': 7}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2", "ABC3"])), ordered=False)

    def test_monthly_alerts(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'notification_frequency': 30}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2", "ABC3", "ABC4", "ABC5"])), ordered=False)

    def test_one_classification(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'classification': ["A"]}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC2"])), ordered=False)
    
    def test_multiple_classification(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'classification': ["A", "B"]}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC2", "ABC3"])), ordered=False)

    def test_all_filters(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'classification': ["B"], "region": "England", "notification_frequency": 7}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1"])), ordered=False)  

    def test_some_filters(self):
        qs = Tender.objects.all()
        f = TenderFilter(data={'classification': ["B"], "notification_frequency": 7}, queryset=qs)
        result = f.qs
        self.assertQuerysetEqual(result, list(Tender.objects.all().filter(uuid__in=["ABC1", "ABC3"])), ordered=False) 