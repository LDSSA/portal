from django.db import migrations


def mark_optional(apps, schema_editor):
    apps.get_model("academy", "Unit").objects.filter(
        code__in=["SLU18", "SLU19", "SLU32", "SLU64"]
    ).update(required_for_certificate=False)


class Migration(migrations.Migration):
    dependencies = [
        ("academy", "0012_unit_required_for_certificate_alter_unit_due_date")
    ]
    operations = [migrations.RunPython(mark_optional, migrations.RunPython.noop)]
