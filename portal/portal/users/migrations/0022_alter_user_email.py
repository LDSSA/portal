# Generated by Django 4.2.14 on 2024-09-15 23:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0021_remove_user_logo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]