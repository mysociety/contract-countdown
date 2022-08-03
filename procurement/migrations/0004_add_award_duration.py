# Generated by Django 4.0.5 on 2022-07-26 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("procurement", "0003_council_codes"),
    ]

    operations = [
        migrations.AddField(
            model_name="award",
            name="duration",
            field=models.IntegerField(
                blank=True, help_text="contract length in days", null=True
            ),
        ),
        migrations.AlterField(
            model_name="award",
            name="tender",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="awards",
                to="procurement.tender",
            ),
        ),
    ]
