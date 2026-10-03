"""The table rendered in admin and used by the executor; no inferred deletions."""

from django.apps import apps

# Ordered child-before-parent deletes. Includes BOTH simulator point models.
CLEAR = (
    "selection.EnrollmentEmail",
    "selection.SelectionDocument",
    "selection.SelectionLogs",
    "selection.Selection",
    "applications.Submission",
    "applications.Application",
    "academy.GradeDeadlineDecision",
    "academy.Grade",
    "hackathons.Submission",
    "hackathons.Attendance",
    "hackathons.Team",
    "capstone.Report",
    "capstone.StudentApi",
    "capstone.DueDatapoint",
    "capstone.Datapoint",
    "capstone.Simulator",
    "users.UserWhitelist",
    "account.EmailConfirmation",
    "sessions.Session",
)
KEEP = (
    "auth.Permission",
    "auth.Group",
    "contenttypes.ContentType",
    "sites.Site",
    "socialaccount.SocialApp",
    "academy.Specialization",
    "academy.Unit",
    "hackathons.Hackathon",
    "capstone.Capstone",
    "applications.Challenge",
)
SELECTIVE = (
    "users.User",
    "account.EmailAddress",
    "socialaccount.SocialAccount",
    "socialaccount.SocialToken",
    "authtoken.Token",
    "admin.LogEntry",
    "constance.Constance",
)
UPDATED_FIELDS = {
    "academy.Unit": {"instructor_id", "open"},
    "hackathons.Hackathon": {"status"},
    "capstone.Capstone": {
        "proposal_open",
        "report_provisory_open",
        "report_final_open",
    },
}
NOTES = {
    "users.User": "Keep the operator, configured service accounts, selected organizers, and student-only or roleless accounts marked for retention during the next edition reset; delete all other users and their database credentials. Marked accounts keep their existing role state, but all previous-edition academic and admissions activity is cleared. Their retention setting resets to false after success.",
    "academy.Unit": "Keep every unit, clear instructor, close submissions; preserve dates, checksum and curriculum metadata.",
    "hackathons.Hackathon": "Keep definitions and files; set status to closed. Preserve dates and scoring settings.",
    "capstone.Capstone": "Keep definitions and scoring references; close all three report submission switches.",
    "applications.Challenge": "Keep reusable exam definitions; old exam attempts are always deleted.",
    "constance.Constance": "Keep dates, mode and unrelated configuration; disable public registration, payments and course access.",
    "admin.LogEntry": "Keep surviving audit entries; entries owned by deleted users cascade away.",
    "authtoken.Token": "Keep retained users' tokens unchanged. Delete tokens belonging to deleted users.",
    "capstone.Datapoint": "Delete all source points associated with historical simulator runs, even when populated.",
    "capstone.DueDatapoint": "Delete all scheduled points, requests and results, even when populated.",
}


def model(label):
    return apps.get_model(label)


def policy_rows():
    rows = []
    for label in sorted(set(CLEAR + KEEP + SELECTIVE)):
        action = (
            "Clear all"
            if label in CLEAR
            else "Keep all; configure"
            if label in UPDATED_FIELDS
            else "Keep all"
            if label in KEEP
            else "Selective / configure"
        )
        note = NOTES.get(
            label,
            "Remove previous-edition activity in both admission modes."
            if label in CLEAR
            else "Preserve reusable configuration."
            if label in KEEP
            else "Keep records associated with retained accounts.",
        )
        rows.append({"model": label, "action": action, "details": note})
    rows += [
        {
            "model": "authtoken.TokenProxy",
            "action": "No separate operation",
            "details": "Proxy of Token; not another table.",
        },
        {
            "model": "django_migrations",
            "action": "Keep all",
            "details": "Migration history is never reset.",
        },
        {
            "model": "edition_management.*",
            "action": "Keep",
            "details": "Operational gate, reset/backup history and job tracking survive.",
        },
    ]
    return rows
