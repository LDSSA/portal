# Generated by Django 3.0.3 on 2020-03-01 18:23

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("applications", "0003_auto_20200214_2350")]

    operations = [
        migrations.AddField(
            model_name="application",
            name="slu01_started_at",
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 21, 0, 0)),
        ),
        migrations.AddField(
            model_name="application",
            name="slu02_started_at",
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 21, 0, 0)),
        ),
        migrations.AddField(
            model_name="application",
            name="slu03_started_at",
            field=models.DateTimeField(default=datetime.datetime(2020, 6, 21, 0, 0)),
        ),
    ]
