# Generated by Django 4.0.5 on 2022-08-04 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("procurement", "0004_add_award_duration"),
    ]

    operations = [
        migrations.CreateModel(
            name="Classification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.CharField(max_length=500)),
                ("classification_scheme", models.CharField(max_length=200)),
                ("group", models.CharField(blank=True, max_length=300, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="TenderClassification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "classification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="procurement.classification",
                    ),
                ),
                (
                    "tender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tenderclassification",
                        to="procurement.tender",
                    ),
                ),
            ],
        ),
    ]
