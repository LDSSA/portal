# Generated by Django 2.2.1 on 2019-07-03 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hackathons", "0005_hackathon_started"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="hackathon",
            name="attendance_open",
        ),
        migrations.RemoveField(
            model_name="hackathon",
            name="complete",
        ),
        migrations.RemoveField(
            model_name="hackathon",
            name="open",
        ),
        migrations.RemoveField(
            model_name="hackathon",
            name="started",
        ),
        migrations.RemoveField(
            model_name="hackathon",
            name="teams_closed",
        ),
        migrations.AddField(
            model_name="hackathon",
            name="status",
            field=models.CharField(
                choices=[
                    ("closed", "Closed"),
                    ("taking_attendance", "Taking Attendance"),
                    ("attendance_closed", "Attendance Closed"),
                    ("marking_presences", "Marking Presences"),
                    ("generating_teams", "Generating Teams"),
                    ("ready", "Ready"),
                    ("submissions_open", "Submissions Open"),
                    ("submissions_closed", "Submissions Closed"),
                    ("complete", "Complete"),
                ],
                default="closed",
                max_length=255,
            ),
        ),
    ]