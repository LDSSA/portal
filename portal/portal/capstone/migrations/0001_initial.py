# Generated by Django 2.2.3 on 2019-11-13 20:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Capstone",
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
                ("name", models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name="Datapoint",
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
                ("data", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="StudentApp",
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
                ("app_name", models.CharField(blank=True, max_length=255)),
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
        migrations.CreateModel(
            name="Simulator",
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
                ("name", models.CharField(max_length=1024)),
                ("started", models.DateTimeField(null=True)),
                ("ends", models.DateTimeField(null=True)),
                ("interval", models.DurationField(null=True)),
                ("endpoint", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("stopped", "stopped"),
                            ("start", "start"),
                            ("started", "started"),
                            ("paused", "paused"),
                            ("reset", "reset"),
                            ("ended", "ended"),
                        ],
                        default="queued",
                        max_length=64,
                    ),
                ),
                (
                    "capstone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="capstone.Capstone",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Score",
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
        migrations.CreateModel(
            name="DueDatapoint",
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
                ("due", models.DateTimeField(null=True)),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("due", "due"),
                            ("queued", "queued"),
                            ("success", "success"),
                            ("fail", "fail"),
                        ],
                        default="duw",
                        max_length=64,
                    ),
                ),
                ("response_content", models.TextField(blank=True)),
                ("response_exception", models.TextField(null=True)),
                ("response_traceback", models.TextField(null=True)),
                ("response_elapsed", models.FloatField(null=True)),
                ("response_status", models.IntegerField(null=True)),
                ("response_timeout", models.BooleanField(default=False)),
                (
                    "datapoint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="capstone.Datapoint",
                    ),
                ),
                (
                    "simulator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="due_datapoints",
                        to="capstone.Simulator",
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
        migrations.AddField(
            model_name="datapoint",
            name="simulator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="datapoints",
                to="capstone.Simulator",
            ),
        ),
    ]
