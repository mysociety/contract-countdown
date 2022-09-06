# Generated by Django 4.0.5 on 2022-09-06 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('procurement', '0008_gss_code_not_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='council',
            name='nation',
            field=models.CharField(default="", max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='council',
            name='region',
            field=models.CharField(default="", max_length=24),
            preserve_default=False,
        ),
    ]
