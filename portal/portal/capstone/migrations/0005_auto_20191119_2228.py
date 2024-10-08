# Generated by Django 2.2.3 on 2019-11-19 22:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("capstone", "0004_auto_20191118_2134"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentApi",
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
                ("url", models.CharField(blank=True, max_length=255)),
                ("score", models.FloatField(default=0)),
                (
                    "capstone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="capstone.Capstone",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="studentapp",
            name="capstone",
        ),
        migrations.RemoveField(
            model_name="studentapp",
            name="student",
        ),
        migrations.RenameField(
            model_name="simulator",
            old_name="endpoint",
            new_name="path",
        ),
        migrations.DeleteModel(
            name="Score",
        ),
        migrations.DeleteModel(
            name="StudentApp",
        ),
    ]
