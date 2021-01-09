
from portal.academy import models as amodels
from portal.hackathons import models as hmodels


for h in (hmodels.Hackathon.objects
          .order_by('code')
          .exclude(code__in=('HCKT0', 'HCKT00'))):
    print(f"\n\n# {h.code}")
    # Check attendance is correct
    teamed_students = []
    hack_students = {a.student for a in h.attendance.all() if a.present}
    teamed_students.extend([s for t in h.teams.all() for s in t.students.all()])
    teamed_students = set(teamed_students)
    # print(teamed_students)
    # print(hack_students)
    if teamed_students != hack_students:
        print("\n## Inconsistencies")
        in_team_but_not_present = teamed_students - hack_students
        present_but_no_team = hack_students - teamed_students
        if in_team_but_not_present:
            print(f"    * In team but not present: {in_team_but_not_present}")
        if present_but_no_team:
            print(f"    * Present but no team {present_but_no_team}")
    # Teams
    for t in h.teams.all():
        print(f"\n## Team {t.hackathon_team_id}")
        for s in t.students.all():
            print(f"    * {s.username}")
    # Missing
    print("\n## Missed hackathon")
    for a in h.attendance.filter(present=False):
        print(f"* {a.student.username}")
    # Submissions
    print("\n## Submissions")
    for sub in h.submissions.order_by('-created'):
        if sub.content_type.model == 'team':
            print(f"    * Team {sub.content_object.hackathon_team_id} - {sub.created}")
        else:
            print(f"    * {sub.content_object.username} - {sub.created}")


for spec in (amodels.Specialization.objects
             .order_by('code').exclude(code='sample')):
    for lu in spec.units.order_by('code'):
        print(f"\n\n {lu.code}")
        for g in lu.grades.filter(status='graded'):
            print(f"    * {g.student.username} {g.score} {g.updated}")
