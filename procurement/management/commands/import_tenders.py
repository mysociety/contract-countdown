import re
from os.path import join
import dateutil.parser

import requests
from pathlib import Path

import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError, DataError

from procurement.models import Council, Tender, Award


class Command(BaseCommand):
    help = "import basic tender data"

    data_file = "data/procurement_data/merged.csv"

    def handle(self, *args, **options):
        self.options = options

        self.import_tenders()

    def get_files(self):
        r = requests.get(settings.PROCUREMENT_DATA)
        with open(self.data_file, "wb") as out:
            out.write(r.content)

    def import_tenders(self):
        self.get_files()
        print("opening csv file")
        df = pd.read_csv(self.data_file)

        for index, row in df.iterrows():
            if pd.isnull(row["local-authority-code"]):
                next

            try:
                council = Council.objects.get(
                    authority_code=row["local-authority-code"]
                )
            except Council.DoesNotExist:
                council = Council(
                    name=row["council"],
                    slug=Council.slugify_name(row["council"]),
                    authority_code=row["local-authority-code"],
                    gss_code=row["gss_code"],
                )
                council.save()

            try:
                tender, created = Tender.objects.get_or_create(
                    uuid=row["id_tender"],
                    council=council,
                )

                value = row["tender_amount"]
                if pd.isnull(value):
                    value = 0

                tender.title = row["tender_title"]
                tender.description = row["tender_description"]
                tender.state = row["tender_status"]
                tender.value = value
                tender.save()
            except IntegrityError as e:
                print(e)
                print(
                    "value row is {}, null result: {}".format(
                        row["value_amount"], pd.isnull(row["value_amount"])
                    )
                )
                next
            except DataError as e:
                print(e)
                title = row["title"]
                if pd.isnull(title):
                    title = ""
                print("title is {} long".format(len(title)))
                next

            award, created = Award.objects.get_or_create(
                uuid=row["id_award"],
                tender=tender,
            )

            award.value = row["award_amount"]
            if not pd.isnull(row["contractPeriod_startDate"]):
                award.start_date = dateutil.parser.parse(
                    row["contractPeriod_startDate"]
                ).date()
            if not pd.isnull(row["contractPeriod_endDate"]):
                award.end_date = dateutil.parser.parse(
                    row["contractPeriod_endDate"]
                ).date()
            award.save()
