# Generated by Django 2.2.1 on 2019-07-01 19:21

import uuid

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
            name="Hackathon",
            fields=[
                (
                    "code",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("open", models.BooleanField(default=False)),
                ("complete", models.BooleanField(default=False)),
                ("max_submissions", models.IntegerField(default=3)),
                ("scoring_fcn", models.TextField(blank=True)),
                ("y_true", models.TextField(blank=True)),
                ("descending", models.BooleanField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Team",
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
                ("hackathon_team_id", models.IntegerField(default=0)),
                ("remote", models.BooleanField(default=False)),
                (
                    "token",
                    models.UUIDField(default=uuid.uuid4, editable=False),
                ),
                ("name", models.TextField(blank=True)),
                ("logo", models.TextField(blank=True)),
                ("submissions", models.IntegerField(default=0)),
                ("score", models.FloatField(default=0.0)),
                (
                    "hackathon",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="hackathons.Hackathon",
                    ),
                ),
                (
                    "students",
                    models.ManyToManyField(
                        related_name="hackathon_teams",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Attendance",
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
                ("will_attend", models.BooleanField(default=False)),
                ("present", models.BooleanField(default=False)),
                ("remote", models.BooleanField(default=False)),
                (
                    "hackathon",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hackathons.Hackathon",
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
    ]
