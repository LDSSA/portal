# Generated by Django 3.1.7 on 2021-03-07 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20210223_1901'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='github_username',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='slack_member_id',
            field=models.TextField(blank=True),
        ),
    ]