# Generated by Django 3.1.7 on 2021-02-23 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("capstone", "0005_auto_20191119_2228"),
    ]

    operations = [
        migrations.AlterField(
            model_name="simulator",
            name="capstone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="simulators",
                to="capstone.capstone",
            ),
        ),
    ]
