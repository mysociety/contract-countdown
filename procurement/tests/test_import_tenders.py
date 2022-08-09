from django.test import TestCase

import unittest
from django.core.management import call_command

from procurement.models import (
    Council,
    Tender,
    Award,
)


class ImportTendersTestCase(TestCase):
    def test_basic_import(self):
        call_command(
            "import_tenders",
            skip_download=True,
            data_file="procurement/tests/data/import_data.csv",
        )

        self.assertEqual(Tender.objects.count(), 1, "correct tender import count")
        self.assertEqual(Council.objects.count(), 1, "correct council import count")
        self.assertEqual(Award.objects.count(), 0, "correct award import count")

        council = Council.objects.first()
        self.assertEqual(council.name, "Sheffield City Council", "correct council name")

        tender = Tender.objects.first()
        self.assertEqual(
            tender.title,
            "Supported Work Placement Service for people living with Autism Spectrum Disorder",
            "correct tender title",
        )
        self.assertEqual(tender.uuid, "20220527180213-104130", "correct tender uuid")
        self.assertEqual(tender.value, 70000.0, "correct tender value")

        classifications = tender.tenderclassification.all()
        self.assertEqual(classifications.count(), 1, "correct classification count")
        classification = classifications[0].classification
        self.assertEqual(
            classification.description,
            "Adult and other education services",
            "correct classification",
        )
        self.assertEqual(classification.group, None, "no classification group assigned")

    def test_import_with_two_items(self):
        call_command(
            "import_tenders",
            skip_download=True,
            data_file="procurement/tests/data/import_data_two_items.csv",
        )

        self.assertEqual(Tender.objects.count(), 1, "correct tender import count")
        self.assertEqual(Council.objects.count(), 1, "correct council import count")
        self.assertEqual(Award.objects.count(), 0, "correct award import count")

        tender = Tender.objects.first()
        classifications = tender.tenderclassification.all()
        self.assertEqual(classifications.count(), 2, "correct classification count")

        classification = classifications[0].classification
        self.assertEqual(
            classification.description,
            "Adult and other education services",
            "correct classification",
        )
        self.assertEqual(classification.group, None, "no classification group assigned")

        classification = classifications[1].classification
        self.assertEqual(
            classification.description,
            "Second classification",
            "correct second classification",
        )
        self.assertEqual(classification.group, None, "no classification group assigned")

    def test_import_with_award(self):
        call_command(
            "import_tenders",
            skip_download=True,
            data_file="procurement/tests/data/import_data_award.csv",
        )

        self.assertEqual(Tender.objects.count(), 1, "correct tender import count")
        self.assertEqual(Council.objects.count(), 1, "correct council import count")
        self.assertEqual(Award.objects.count(), 1, "correct award import count")

        tender = Tender.objects.first()
        award = Award.objects.all()[0]
        self.assertEqual(award.tender, tender, "award has correct tender")
        self.assertEqual(award.uuid, "1", "award has correct uuid")
        self.assertEqual(award.value, 70000.0, "award has correct value")
        self.assertEqual(
            award.start_date.isoformat(), "2022-07-10", "award has correct start date"
        )
        self.assertEqual(
            award.end_date.isoformat(), "2022-08-10", "award has correct end_date"
        )
        self.assertEqual(award.duration, 31, "award has correct duration")

    def test_import_with_two_awards(self):
        call_command(
            "import_tenders",
            skip_download=True,
            data_file="procurement/tests/data/import_data_two_awards.csv",
        )

        self.assertEqual(Tender.objects.count(), 1, "correct tender import count")
        self.assertEqual(Council.objects.count(), 1, "correct council import count")
        self.assertEqual(Award.objects.count(), 2, "correct award import count")

        tender = Tender.objects.first()
        award = Award.objects.all()[0]
        self.assertEqual(award.tender, tender, "award has correct tender")
        self.assertEqual(award.uuid, "award-1", "award has correct uuid")
        self.assertEqual(award.value, 30000.0, "award has correct value")
        self.assertEqual(
            award.start_date.isoformat(), "2022-07-10", "award has correct start date"
        )
        self.assertEqual(
            award.end_date.isoformat(), "2022-08-10", "award has correct end_date"
        )
        self.assertEqual(award.duration, 31, "award has correct duration")

        award = Award.objects.all()[1]
        self.assertEqual(award.tender, tender, "award has correct tender")
        self.assertEqual(award.uuid, "award-2", "award has correct uuid")
        self.assertEqual(award.value, 40000.0, "award has correct value")
        self.assertEqual(
            award.start_date.isoformat(), "2022-08-10", "award has correct start date"
        )
        self.assertEqual(
            award.end_date.isoformat(), "2022-09-10", "award has correct end_date"
        )
        self.assertEqual(award.duration, 31, "award has correct duration")
