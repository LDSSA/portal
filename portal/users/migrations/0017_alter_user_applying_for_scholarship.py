# Generated by Django 3.2.3 on 2021-06-08 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_auto_20210608_2019"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="applying_for_scholarship",
            field=models.BooleanField(default=None, null=True),
        ),
    ]