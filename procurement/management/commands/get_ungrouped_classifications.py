import json
from os.path import join

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError, DataError

from procurement.models import Classification


class Command(BaseCommand):
    help = "import basic tender data"

    data_file = "data/procurement_data/merged.csv"
    groups_file = "data/groups.json"

    def handle(self, *args, **options):
        self.options = options

        self.get_groups()
        self.get_ungrouped()

    def get_groups(self):
        with open(self.groups_file, "r") as groups:
            data = json.load(groups)

        self.groups = {}
        for group, members in data.items():
            for member in members:
                self.groups[member] = group

    def get_ungrouped(self):
        ungrouped = (
            Classification.objects.filter(group__isnull=True)
            .distinct("description")
            .all()
            .values_list("description", flat=True)
        )

        ungrouped = [x for x in ungrouped]
        with open("data/ungrouped.json", "w") as out:
            json.dump(ungrouped, out, indent=4)
