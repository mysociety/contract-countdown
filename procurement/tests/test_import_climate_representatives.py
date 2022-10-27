from django.test import TestCase

import unittest
from django.core.management import call_command

from procurement.models import (
    Council,
    ClimateRepresentative,
)


class ImportClimateRepresentativesTestCase(TestCase):
    def setUp(self):
        kingshol_council = Council.objects.create(
            name="Kingshol County Council",
            slug="kingshol-county-council",
            authority_code="KBC",
            gss_code="N01232343",
            nation="Northern Ireland",
            region="Northern Ireland",
        )

        stanelsaints_council = Council.objects.create(
            name="Stanelsaints County Council",
            slug="stanelsaints-county-council",
            authority_code="STS",
            gss_code="W01554545",
            nation="Wales",
            region="Wales",
        )

        north_slandwark_council = Council.objects.create(
            name="North Slandwark Council",
            slug="north-slandwark-council",
            authority_code="NSC",
            gss_code="W09999999",
            nation="Wales",
            region="Wales",
        )

        hodrish_council = Council.objects.create(
            name="Hodrish Council",
            slug="hodrish-council",
            authority_code="HOD",
            gss_code="W93948582",
            nation="Wales",
            region="Wales",
        )

        didun_council = Council.objects.create(
            name="Didun Council",
            slug="didun-council",
            authority_code="DDN",
            gss_code="S45111143",
            nation="Scotland",
            region="Scotland",
        )

        sheadsophi_council = Council.objects.create(
            name="Sheadsophi Council",
            slug="sheadsophi-council",
            authority_code="SHS",
            gss_code="E45321567",
            nation="England",
            region="Wales",
        )
        clunnkridge_council = Council.objects.create(
            name="Clunnkridge Council",
            slug="clunnkridge-council",
            authority_code="CLN",
            gss_code="S09432369",
            nation="Scotland",
            region="Scotland",
        )


    def test_basic_import(self):
        call_command(
            "import_climate_representatives",
            officers_file="procurement/tests/data/climate_representative_import/import_climate_officers_basic.csv",
            councillors_file="procurement/tests/data/climate_representative_import/import_climate_councillors_basic.csv",
        )

        self.assertEqual(
            ClimateRepresentative.objects.count(),
            2,
            "correct representative import count",
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="officer").count(), 1, "correct officer import count"
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="councillor").count(), 1, "correct councillor import count"
        )

        officer = ClimateRepresentative.objects.filter(representative_type="officer").first()
        self.assertEqual(officer.first_name, "Patrick", "correct officer name")
        self.assertEqual(
            officer.email,
            "patrick.weber@kingsholboroughcouncil.gov.uk",
            "correct officer email address",
        )

        councillor = ClimateRepresentative.objects.filter(representative_type="councillor").first()
        self.assertEqual(councillor.first_name, "Daniel", "correct councillor name")
        self.assertEqual(
            councillor.email,
            "daniel.spencer@kingsholboroughcouncil.gov.uk",
            "correct councillor email address",
        )

    def test_import_with_multiples(self):
        call_command(
            "import_climate_representatives",
            officers_file="procurement/tests/data/climate_representative_import/import_climate_officers_multiple.csv",
            councillors_file="procurement/tests/data/climate_representative_import/import_climate_councillors_multiple.csv",
        )

        self.assertEqual(
            ClimateRepresentative.objects.count(),
            8,
            "correct representative import count",
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="officer").count(), 4, "correct officer import count"
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="councillor").count(), 4, "correct councillor import count"
        )

        officer = ClimateRepresentative.objects.filter(representative_type="officer").first()
        self.assertEqual(officer.first_name, "Patrick", "correct officer name")
        self.assertEqual(
            officer.email,
            "patrick.weber@kingsholboroughcouncil.gov.uk",
            "correct officer email address",
        )

        councillor = ClimateRepresentative.objects.filter(representative_type="councillor").first()
        self.assertEqual(councillor.first_name, "Daniel", "correct councillor name")
        self.assertEqual(
            councillor.email,
            "daniel.spencer@kingsholboroughcouncil.gov.uk",
            "correct councillor email address",
        )

    def test_import_with_bad_values(self):
        # Null values in columns we want stop the entire row from getting imported.
        call_command(
            "import_climate_representatives",
            officers_file="procurement/tests/data/climate_representative_import/import_climate_officers_bad_data.csv",
            councillors_file="procurement/tests/data/climate_representative_import/import_climate_councillors_bad_data.csv",
        )

        self.assertEqual(
            ClimateRepresentative.objects.count(),
            2,
            "correct representative import count",
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="officer").count(), 1, "correct officer import count"
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="councillor").count(), 1, "correct councillor import count"
        )

    def test_councils_imported_correctly(self):
        call_command(
            "import_climate_representatives",
            officers_file="procurement/tests/data/climate_representative_import/import_climate_officers_councils.csv",
            councillors_file="procurement/tests/data/climate_representative_import/import_climate_councillors_councils.csv",
        )

        self.assertEqual(
            ClimateRepresentative.objects.count(),
            4,
            "correct representative import count",
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="officer").count(), 2, "correct officer import count"
        )
        self.assertEqual(
            ClimateRepresentative.objects.filter(representative_type="councillor").count(), 2, "correct councillor import count"
        )

        councillors_test_dict = {
            "Hugo": Council.objects.get(gss_code="W09999999"),
            "Vikki": Council.objects.get(gss_code="W01554545"),
        }

        officers_test_dict = {
            "Melina": Council.objects.get(gss_code="W09999999"),
            "Kasper": Council.objects.get(gss_code="W93948582"),
        }

        for councillor in ClimateRepresentative.objects.filter(representative_type="councillor"):
            self.assertEqual(
                councillor.council,
                councillors_test_dict[councillor.first_name],
                "correct Council",
            )
        for officer in ClimateRepresentative.objects.filter(representative_type="officer"):
            self.assertEqual(
                officer.council,
                officers_test_dict[officer.first_name],
                "correct Council",
            )
