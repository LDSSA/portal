# Generated by Django 2.0.13 on 2019-03-10 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="student",
            field=models.BooleanField(default=True),
        ),
    ]