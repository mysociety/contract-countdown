from django.test import TestCase
from datetime import date, timedelta

import unittest

from procurement.models import (
    Council,
    Tender,
    Award,
)


class ModelsTestCase(TestCase):
    def test_current_award(self):
        today = date.today()
        start = today - timedelta(days=20)
        end = today + timedelta(days=10)

        award = Award(
            uuid="award-1",
            value="20",
            date=start,
            start_date=start,
            end_date=end,
            duration=30,
        )

        self.assertTrue(award.contract_current())
        self.assertTrue(award.contract_started())
        self.assertFalse(award.contract_ended())
        self.assertEquals(award.contract_length().days, 30)
        self.assertEquals(award.contract_length_desc(), "30 day contract")
        self.assertEquals(int(award.contract_percent_complete()), 66)
        self.assertEquals(award.contract_time_remaining_desc(), "10 days left")

    def test_ended_award(self):
        today = date.today()
        start = today - timedelta(days=40)
        end = today - timedelta(days=10)

        award = Award(
            uuid="award-1",
            value="20",
            date=start,
            start_date=start,
            end_date=end,
            duration=30,
        )

        self.assertFalse(award.contract_current())
        self.assertTrue(award.contract_started())
        self.assertTrue(award.contract_ended())
        self.assertEquals(award.contract_length().days, 30)
        self.assertEquals(award.contract_length_desc(), "30 day contract")
        self.assertEquals(int(award.contract_percent_complete()), 100)
        self.assertEquals(
            award.contract_time_remaining_desc(),
            "Contract ends: {}".format(end.isoformat()),
        )

    def test_future_award(self):
        today = date.today()
        start = today + timedelta(days=20)
        end = today + timedelta(days=80)

        award = Award(
            uuid="award-1",
            value="20",
            date=start,
            start_date=start,
            end_date=end,
            duration=60,
        )

        self.assertFalse(award.contract_current())
        self.assertFalse(award.contract_started())
        self.assertFalse(award.contract_ended())
        self.assertEquals(award.contract_length().days, 60)
        self.assertEquals(award.contract_length_desc(), "2 month contract")
        self.assertEquals(int(award.contract_percent_complete()), 0)
        self.assertEquals(
            award.contract_time_remaining_desc(),
            "Contract starts: {}".format(start.isoformat()),
        )
