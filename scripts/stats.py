from portal.academy import models as amodels  # noqa: D100
from portal.hackathons import models as hmodels

for h in hmodels.Hackathon.objects.order_by("code").exclude(code__in=("HCKT0", "HCKT00")):
    print(f"\n\n# {h.code}")  # noqa: T201
    # Check attendance is correct
    teamed_students = []
    hack_students = {a.student for a in h.attendance.all() if a.present}
    teamed_students.extend([s for t in h.teams.all() for s in t.users.all()])
    teamed_students = set(teamed_students)
    if teamed_students != hack_students:
        print("\n## Inconsistencies")  # noqa: T201
        in_team_but_not_present = teamed_students - hack_students
        present_but_no_team = hack_students - teamed_students
        if in_team_but_not_present:
            print(f"    * In team but not present: {in_team_but_not_present}")  # noqa: T201
        if present_but_no_team:
            print(f"    * Present but no team {present_but_no_team}")  # noqa: T201
    # Teams
    for t in h.teams.all():
        print(f"\n## Team {t.hackathon_team_id}")  # noqa: T201
        for s in t.users.all():
            print(f"    * {s.username}")  # noqa: T201
    # Missing
    print("\n## Missed hackathon")  # noqa: T201
    for a in h.attendance.filter(present=False):
        print(f"* {a.student.username}")  # noqa: T201
    # Submissions
    print("\n## Submissions")  # noqa: T201
    for sub in h.submissions.order_by("-created"):
        if sub.content_type.model == "team":
            print(  # noqa: T201
                f"    * Team {sub.content_object.hackathon_team_id} - {sub.created}"
            )
        else:
            print(f"    * {sub.content_object.username} - {sub.created}")  # noqa: T201


for spec in amodels.Specialization.objects.order_by("code").exclude(code="sample"):
    for lu in spec.units.order_by("code"):
        print(f"\n\n {lu.code}")  # noqa: T201
        for g in lu.grades.filter(status="graded"):
            print(f"    * {g.student.username} {g.score} {g.updated}")  # noqa: T201
