from django.db import migrations, models


def initialize_roleless_reset_retention(apps, schema_editor):
    User = apps.get_model("users", "User")
    may_choose = models.Q(
        is_staff=False,
        is_superuser=False,
        is_instructor=False,
    )
    User.objects.filter(
        may_choose,
        retain_account_on_next_edition_reset__isnull=True,
    ).update(retain_account_on_next_edition_reset=False)
    User.objects.exclude(may_choose).update(retain_account_on_next_edition_reset=None)


def restore_student_only_reset_retention(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(
        is_student=False,
        is_staff=False,
        is_superuser=False,
        is_instructor=False,
    ).update(retain_account_on_next_edition_reset=None)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0024_student_reset_retention"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="users_student_reset_retention_matches_role",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="retain_student_account_on_next_edition_reset",
            new_name="retain_account_on_next_edition_reset",
        ),
        migrations.AlterField(
            model_name="user",
            name="retain_account_on_next_edition_reset",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text="Student-only and roleless accounts: select to preserve the complete user account during the next edition reset. The student's role, when present, is preserved, but academic and admissions activity is still deleted. After a successful reset, this setting returns to unselected and must be authorized again for a later reset. Staff, superusers, instructors, and mixed-role accounts use the organizer policy instead.",
                null=True,
                verbose_name="Retain account on next edition reset",
            ),
        ),
        migrations.RunPython(
            initialize_roleless_reset_retention,
            restore_student_only_reset_retention,
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                name="users_reset_retention_matches_role",
                check=(
                    models.Q(
                        is_staff=False,
                        is_superuser=False,
                        is_instructor=False,
                        retain_account_on_next_edition_reset__isnull=False,
                    )
                    | (
                        ~models.Q(
                            is_staff=False,
                            is_superuser=False,
                            is_instructor=False,
                        )
                        & models.Q(retain_account_on_next_edition_reset__isnull=True)
                    )
                ),
            ),
        ),
    ]
