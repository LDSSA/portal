# Generated by Django 3.2.3 on 2021-06-02 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0011_alter_challenge_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="checksum",
            field=models.TextField(blank=True),
        ),
    ]