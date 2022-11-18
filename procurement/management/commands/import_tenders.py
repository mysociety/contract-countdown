import re
import json
from os.path import join
import time
import dateutil.parser
from datetime import datetime, timedelta, timezone, date
import http

import urllib3
import requests
from pathlib import Path

import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError, DataError

from mysoc_dataset import get_dataset_url, get_dataset_df

from procurement.models import (
    Council,
    Tender,
    Award,
    Classification,
    TenderClassification,
)


class Command(BaseCommand):
    help = "import basic tender data"

    groups_file = "data/groups.json"
    groups = {}

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--get_all", action="store_true", help="Get all tender data"
        )
        group.add_argument("--update", action="store_true", help="Get new tender data")

    def handle(self, *args, **options):
        self.options = options
        self.params = self.set_params()
        self.get_groups()
        if options["get_all"]:
            # If we're getting all of the objects, delete any that may
            # already be there.
            delete = Tender.objects.all().delete()
            delete = delete[1].get("procurement.Tender", 0)
            print(f"{delete} tenders deleted.")
        self.get_council_lookup_df()
        df = self.create_combined_dataframe()
        self.import_tenders(df)

    def set_params(self):
        published_from = "2020-01-01T00:00:00+00:00"
        if self.options["update"]:
            # Get the most recently published tender in the db
            if Tender.objects.all().exists():
                published_to = str(
                    Tender.objects.filter(published__isnull=False).latest("published").published
                )
                published_from = dateutil.parser.parse(published_to).isoformat()
            else:
                print("No Tender objects in database! Downloading all.")
        contracts_finder_uri = f"https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?publishedFrom={published_from}&stages=award"
        find_tender_uri = f"https://www-integration.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?updatedFrom={published_from}&stages=award"
        
        self.contracts_finder_uri = contracts_finder_uri
        self.find_tender_uri = find_tender_uri

    def get_council_lookup_df(self):
        self.council_lookup = get_dataset_df(
            repo_name="uk_local_authority_names_and_codes",
            package_name="uk_la_past_current",
            version_name="1",
            file_name="lookup_name_to_registry.csv",
        )

    def get_groups(self):
        with open(self.groups_file, "r") as groups:
            data = json.load(groups)

        self.groups = {}
        for group, members in data.items():
            for member in members:
                self.groups[member] = group

    def create_combined_dataframe(self):
        # Get the data from find_tender
        print("Loading Find-Tender data.")
        find_tender_df = self.get_data_from_api(self.find_tender_uri)
        print("Loading Contract Finder data.")
        contract_finder_df = self.get_data_from_api(self.contracts_finder_uri)
        return pd.concat([find_tender_df, contract_finder_df])

    def get_date_from_str(self, date_string):
        if not pd.isnull(date_string):
            return dateutil.parser.parse(date_string).date()

        return None

    def import_tenders(self, df):
        print("Wrangling data.")
        # First, drop all rows with a classification that isn't in groups.json
        classification_descriptions_in_groups = self.groups.keys()
        df = df.query(
            "tender_classification_description in @classification_descriptions_in_groups"
        )
        # Next, merge with councils data to drop all rows not from a local authority
        df = df.merge(
            self.council_lookup, left_on="buyer_name", right_on="la-name", how="inner"
        )
        df = df.query("tender_status == 'complete'").reset_index(drop=True)
        # Reindex the df with all required columns so that if they don't show up
        # from the raw data, they still exist in the df (filled with NaNs), so that
        # they don't break the code that reads them into the db.
        columns_list = [
            "ocid",
            "tender_title",
            "tender_description",
            "tender_status",
            "tender_value_amount",
            "date",
            "tender_tenderPeriod_startDate",
            "tender_tenderPeriod_endDate",
            "tender_classification_scheme",
            "tender_classification_description",
            "la-name",
            "local-authority-code",
            "awards",
        ]
        df = df.reindex(columns=columns_list)
        df.tender_tenderPeriod_startDate = df.tender_tenderPeriod_startDate.apply(
            self.get_date_from_str
        )
        df.tender_tenderPeriod_endDate = df.tender_tenderPeriod_endDate.apply(
            self.get_date_from_str
        )
        df.date = df.date.apply(self.get_date_from_str)

        classification_df = df[
            ["tender_classification_scheme", "tender_classification_description"]
        ].drop_duplicates()
        classification_df[
            "group"
        ] = classification_df.tender_classification_description.map(self.groups)
        for index, row in classification_df.iterrows():
            classification, created = Classification.objects.get_or_create(
                description=row.tender_classification_description,
                classification_scheme=row.tender_classification_scheme,
                group=row.group,
            )

        # Create tenders df
        tender_cols = ["local-authority-code", "ocid", "date", "awards"]
        tender_cols.extend([col for col in df.columns if "tender_" in col])
        tenders_df = df[tender_cols].dropna(subset=["awards", "ocid"])

        # Very naive way of getting most up to date release data. Drops duplicates on: ocid first,
        # to remove duplicates in the same record, and then title next to remove duplicates between
        # the two APIs.
        tenders_df = (
            tenders_df.sort_values("date")
            .drop_duplicates("ocid")
            .drop_duplicates("tender_title")
        )

        # Get awards
        awards = tenders_df.set_index("ocid").awards
        awards = awards.explode().apply(pd.Series)
        awards["amount"] = awards.value.str["amount"]
        awards["start_date"] = awards.contractPeriod.str["startDate"].apply(
            self.get_date_from_str
        )
        awards["end_date"] = awards.contractPeriod.str["endDate"].apply(
            self.get_date_from_str
        )
        awards["datePublished"] = pd.to_datetime(awards.datePublished)
        awards = awards.add_prefix("award_")
        awards = awards.reset_index()
        tenders_df = tenders_df.merge(awards, on="ocid", how="inner").drop(
            columns=["award_contractPeriod", "award_value"]
        )

        today = date.today()
        tenders_df = tenders_df.query("award_end_date > @today")

        tenders_df = tenders_df.sort_values("award_datePublished").drop_duplicates(
            subset=["ocid", "award_id"]
        )
        tenders_df = tenders_df.groupby("ocid").nth(0).reset_index()
        print("Loading tenders and awards into database.")
        tenders_count = 0
        awards_count = 0
        for index, row in tenders_df.iterrows():
            tender, created = Tender.objects.update_or_create(
                uuid=row.ocid,
                title=row.tender_title,
                description=row.tender_description,
                state=row.tender_status,
                published=row.date,
                council=Council.objects.get(authority_code=row["local-authority-code"]),
            )
            if pd.notna(row.tender_tenderPeriod_startDate):
                tender.start_date = row.tender_tenderPeriod_startDate
            if pd.notna(row.tender_tenderPeriod_endDate):
                tender.end_date = row.tender_tenderPeriod_endDate
            tender.save()
            if created:
                tenders_count += 1

            (
                tender_classification,
                tender_classification_created,
            ) = TenderClassification.objects.get_or_create(
                tender=tender,
                classification=Classification.objects.get(
                    description=row.tender_classification_description
                ),
            )
            award, award_created = Award.objects.get_or_create(
                uuid=row.award_id,
                tender=tender,
            )
            award.value=row.award_amount
            tender.value = row.award_amount
            award.tender=tender
            if pd.notna(row.award_datePublished):
                award.date = row.award_datePublished
            if pd.notna(row.award_start_date):
                award.start_date = row.award_start_date
                tender.start_date = row.award_start_date
                tender.save()
            if pd.notna(row.award_end_date):
                award.end_date = row.award_end_date

            if award.start_date and award.end_date:
                award.duration = award.contract_length().days
                award.save()
            if award_created:
                awards_count += 1

        print(f"{tenders_count} tenders created. {awards_count} awards created.")

        delete = Tender.objects.filter(end_date__gt=date.today()).delete()
        delete = delete[1].get("procurement.Tender", 0)
        print(f"{delete} tenders (and associated awards) that have finished have been deleted.")
        print(f"{Tender.objects.all().count()} tenders in the database.")
    def get_data_from_api(self, starting_api_url):
        retries = 0
        api_url = starting_api_url
        json_list = []
        while True:
            try:
                response = requests.get(api_url)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
            ) as e:
                if retries < 3:
                    errormessage = str(e)
                    print(f"{errormessage}. Sleeping for 10 seconds, and trying again.")
                    time.sleep(10)
                    retries += 1
                    continue
                else:
                    print("Too many retries. Giving up.")
                    break
            if response.status_code != 200:
                if response.status_code == 403:
                    print(
                        "Too many requests made. Sleeping for 5 minutes, and trying again."
                    )
                    time.sleep(5 * 60)
                    continue
                if retries < 3:
                    status = str(response.status_code)
                    print(
                        f"Unexpected status code: {status}. Sleeping for 15 seconds, and trying again."
                    )
                    time.sleep(15)
                    retries += 1
                    continue
                else:
                    print("Too many retries. Giving up.")
                    break
            else:
                json = response.json()
                json_list.extend(json["releases"])

                if "cursor" in json.get("links", {}).get("next", ""):
                    api_url = json["links"]["next"]
                else:
                    break
        df = pd.json_normalize(json_list)
        df.columns = df.columns.str.replace(".", "_", regex=False)
        return df
