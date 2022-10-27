import re
import json

import requests
from pathlib import Path

import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError, DataError

from procurement.models import Council, ClimateRepresentative


class Command(BaseCommand):
    help = "import climate councillors and officers"

    officers_file = "data/procurement_data/comeval_officers.csv"
    councillors_file = "data/procurement_data/comeval_councillors.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--officers_file",
            action="store_true",
            help="provide alternative officers data file",
        )

        parser.add_argument(
            "--councillors_file",
            action="store_true",
            help="provide alternative councillors data file",
        )

    def handle(self, *args, **options):
        self.options = options

        if options["officers_file"]:
            self.officers_file = options["officers_file"]

        if options["councillors_file"]:
            self.councillors_file = options["councillors_file"]
        self.get_df()
        self.import_councilors_officers()

    def get_df(self):

        officers_df = pd.read_csv(
            self.officers_file,
            usecols=[
                "title",
                "firstName",
                "surname",
                "type",
                "email",
                "jobTitle",
                "phone",
                "local-authority-code",
                "address",
            ],
        )
        councillors_df = pd.read_csv(
            self.councillors_file,
            usecols=[
                "title",
                "firstName",
                "surname",
                "type",
                "email",
                "genericPositionLocalList",
                "partyAffiliation",
                "councilGssNumber",
            ],
        )
        self.climate_df = pd.concat([officers_df.dropna(), councillors_df.dropna()])

    def import_councilors_officers(self):
        fail_count = 0
        for index, row in self.climate_df.iterrows():
            try:
                representative = ClimateRepresentative(
                    title=row.title,
                    first_name=row.firstName,
                    surname=row.surname,
                    email=row.email,
                )
                if row.type == "Officer":
                    representative.council = Council.objects.get(
                        authority_code=row["local-authority-code"]
                    )
                    representative.job_title = row.jobTitle
                    representative.phone_number = row.phone
                    representative.address = row.address
                    representative.representative_type="officer"         
                else:    
                    representative.council = Council.objects.get(gss_code=row.councilGssNumber)
                    representative.job_title = row.genericPositionLocalList
                    representative.party_affiliation = row.partyAffiliation
                    representative.representative_type="councillor"
                    
                representative.save()
                representative.slug = ClimateRepresentative.slugify_name(representative.id)
                representative.save()

                

            except Council.DoesNotExist:
                fail_count += 1
        print("Fail count: " + str(fail_count))
