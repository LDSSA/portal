# Generated by Django 3.0.3 on 2020-05-11 18:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("applications", "0005_auto_20200509_2034")]

    operations = [
        migrations.AddField(
            model_name="application",
            name="application_over_email_sent",
            field=models.CharField(
                choices=[("passed", "failed")],
                default=None,
                max_length=10,
                null=True,
            ),
        )
    ]
