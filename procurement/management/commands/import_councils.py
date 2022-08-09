import re
import json

import requests
from pathlib import Path

import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError, DataError

from procurement.models import Council


def get_dataset_url(repo: str, package: str, version: str, file: str):
    """
    Get url to a dataset from the mysociety.github.io website.
    """
    return f"https://mysociety.github.io/{repo}/data/{package}/{version}/{file}"


def get_dataset_df(repo: str, package: str, version: str, file: str):
    """
    Get a dataframe from a dataset from the mysociety.github.io website.
    """
    url = get_dataset_url(repo, package, version, file)
    return pd.read_csv(url)


class Command(BaseCommand):
    help = "import councils"

    def handle(self, *args, **options):
        self.get_council_df()
        self.import_councils()

    def get_council_df(self):
        self.council_data = get_dataset_df(
            repo="uk_local_authority_names_and_codes",
            package="uk_la_past_current",
            version="1",
            file="uk_local_authorities_current.csv",
        )

    def import_councils(self):
        for index, row in self.council_data.iterrows():
            if pd.isnull(row["local-authority-code"]):
                next

            try:
                council = Council.objects.get(
                    authority_code=row["local-authority-code"]
                )
            except Council.DoesNotExist:
                council = Council(
                    name=row["official-name"],
                    slug=Council.slugify_name(row["official-name"]),
                    authority_code=row["local-authority-code"],
                    gss_code=row["gss-code"],
                )
                council.save()
