# Generated by Django 3.2.3 on 2021-05-23 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0006_application_application_over_email_sent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]