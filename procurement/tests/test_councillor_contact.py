from django.test import TestCase, Client
from datetime import date, timedelta

import unittest

from django.core.management import call_command
from django.urls import reverse

from procurement.models import ClimateRepresentative, Council

from procurement.forms import ContactPostcodeForm, ContactRepresentativeForm


class TestContactClimateRepresentativeTestCase(TestCase):
    def setUp(self):
        bristol_council = Council.objects.create(
            name="Ceredigion County Council",
            slug="ceredigion-county-council",
            authority_code="CGN",
            gss_code="W06000008",
            nation="Wales",
            region="Wales",
        )
        ceredigion_council = Council.objects.create(
            name="Bristol City Council",
            slug="bristol-city-council",
            authority_code="BST",
            gss_code="E06000023",
            nation="England",
            region="South West",
        )
        call_command(
            "import_climate_representatives",
            officers_file="procurement/tests/data/climate_officer_data_test.csv",
            councillors_file="procurement/tests/data/climate_councillor_data_test.csv",
        )

    def test_representative_models_slugs(self):
        councillor = ClimateRepresentative.objects.filter(
            representative_type="councillor"
        ).first()
        officer = ClimateRepresentative.objects.filter(
            representative_type="officer"
        ).first()

        self.assertEqual(councillor.slug, "46", "correct councillor slug")
        self.assertEqual(officer.slug, "43", "correct officer slug")

    def test_council_contract_view(self):
        response = self.client.get(
            reverse("contact_council", args=["ceredigion-county-council"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["officers"],
            ClimateRepresentative.objects.filter(first_name="Jordan"),
            ordered=False,
        )
        self.assertQuerysetEqual(
            response.context["councillors"],
            ClimateRepresentative.objects.filter(first_name__in=["Sam", "Sue"]),
            ordered=False,
        )

        response = self.client.get(
            reverse("contact_council", args=["bristol-city-council"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["officers"],
            ClimateRepresentative.objects.filter(first_name__in=["Joe", "Jane"]),
            ordered=False,
        )
        self.assertQuerysetEqual(
            response.context["councillors"],
            ClimateRepresentative.objects.filter(first_name="Steve"),
            ordered=False,
        )

    def test_false_slugs(self):
        response = self.client.get(reverse("contact_council", args=["made-up-council"]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "contact_representative",
                kwargs={
                    "council": "ceredigion-county-council",
                    "representative": "made-up",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "contact_representative",
                kwargs={
                    "council": "made-up-council",
                    "representative": "46",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "contact_representative",
                kwargs={"council": "made-up-council", "representative": "made-up"},
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "contact_representative",
                kwargs={"council": "bristol-city-council", "representative": "46"},
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "preview",
                kwargs={"council": "bristol-city-council", "representative": "46"},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_postcode_search_form_valid(self):
        valid_postcodes = ["SW1A 0AA", "cf101ag"]
        for postcode in valid_postcodes:
            data = {"pc": postcode}
            form = ContactPostcodeForm(data=data)
            self.assertTrue(form.is_valid())

    def test_postcode_search_form_invalid(self):
        invalid_postcodes = ["hello world", "KY34 9QZ"]
        for postcode in invalid_postcodes:
            data = {"pc": postcode}
            form = ContactPostcodeForm(data=data)
            self.assertFalse(form.is_valid())

    def test_councillor_contact_form_valid(self):
        valid_data = [
            {  # Test a fully filled out, correct, form
                "message": "message!",
                "name": "Joe Bloggs",
                "email": "abc@gmail.com",
                "email_check": "abc@gmail.com",
                "phone": "01234 123 123",
                "address_1": "Place",
                "address_2": "Street",
                "town_city": "City",
                "county": "County",
                "pc": "SW1A 0AA",
            },
            {  # Test no errors are thrown when non-optional fields aren't filled
                "message": "message!",
                "name": "Joe Bloggs",
                "email": "abc@gmail.com",
                "email_check": "abc@gmail.com",
                "address_1": "Place",
                "town_city": "City",
                "pc": "SW1A 0AA",
            },
        ]
        for data in valid_data:
            form = ContactRepresentativeForm(data=data)
            self.assertTrue(form.is_valid())

    def test_councillor_contact_form_invalid(self):
        invalid_data = [
            {  # Test a form with missing values
                "message": "message!",
            },
            {  # Test form with invalid values wherever they can be
                "message": "message!",
                "name": "Joe Bloggs",
                "email": "abc",
                "email_check": "ab",
                "phone": "phone number",
                "address_1": "Place",
                "address_2": "Street",
                "town_city": "City",
                "county": "County",
                "pc": "postcode",
            },
            {  # Test single invalid field
                "message": "message!",
                "name": "Joe Bloggs",
                "email": "abc@gmail.com",
                "email_check": "abc@gmail.com",
                "phone": "phone number",
                "address_1": "Place",
                "address_2": "Street",
                "town_city": "City",
                "county": "County",
                "pc": "SW1A 0AA",
            },
            {  # Test multi-field validation
                "message": "message!",
                "name": "Joe Bloggs",
                "email": "abc@gmail.com",
                "email_check": "ac@gmail.com",
                "phone": "01234 123 123",
                "address_1": "Place",
                "address_2": "Street",
                "town_city": "City",
                "county": "County",
                "pc": "SW1A 0AA",
            },
        ]
        for data in invalid_data:
            form = ContactRepresentativeForm(data=data)
            self.assertFalse(form.is_valid())

    def test_no_form_data_found_in_session_in_preview(self):
        response = self.client.get(
            reverse(
                "preview",
                kwargs={"council": "ceredigion-county-council", "representative": "46"},
            )
        )
        self.assertEqual(response.status_code, 404)
