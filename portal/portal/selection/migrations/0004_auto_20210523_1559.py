# Generated by Django 3.2.3 on 2021-05-23 15:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("selection", "0003_auto_20200606_1344"),
    ]

    operations = [
        migrations.AlterField(
            model_name="selection",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="selectiondocument",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="selectionlogs",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]
