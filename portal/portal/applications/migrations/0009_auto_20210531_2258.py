# Generated by Django 3.2.3 on 2021-05-31 22:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("applications", "0008_auto_20210527_1819"),
    ]

    operations = [
        migrations.RenameField(
            model_name="submission",
            old_name="file",
            new_name="notebook",
        ),
        migrations.RenameField(
            model_name="submission",
            old_name="challenge",
            new_name="unit",
        ),
        migrations.AddField(
            model_name="submission",
            name="message",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="submission",
            name="status",
            field=models.CharField(
                choices=[
                    ("grading", "Grading"),
                    ("failed", "Grading failed"),
                    ("graded", "Graded"),
                ],
                default="never-submitted",
                max_length=1024,
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.user",
            ),
            preserve_default=False,
        ),
    ]
