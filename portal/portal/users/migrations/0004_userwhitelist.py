# Generated by Django 2.2.1 on 2019-06-08 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_auto_20190421_1603"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserWhitelist",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "username",
                    models.CharField(max_length=255, verbose_name="Username"),
                ),
                ("student", models.BooleanField(default=True)),
            ],
        ),
    ]