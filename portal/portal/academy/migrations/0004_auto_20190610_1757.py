# Generated by Django 2.2.1 on 2019-06-10 17:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academy", "0003_auto_20190610_1442"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grade",
            name="status",
            field=models.CharField(
                choices=[
                    ("never-submitted", "Unsubmitted"),
                    ("grading", "Grading"),
                    ("failed", "Grading failed"),
                    ("out-of-date", "Out-of-date"),
                    ("graded", "Graded"),
                ],
                default="never-submitted",
                max_length=1024,
            ),
        ),
    ]
