from django.db.models import Sum  # noqa: D100

from portal.academy import models
from portal.users.models import User

qs = (
    User.objects.filter(student=True)
    .annotate(total=Sum("grades__score"))
    .order_by("-total")
    .values_list("username", "total")
)
for item in qs:
    print(item)  # noqa: T201


for u in models.Unit.objects.order_by("-code"):
    num = u.grades.filter(status="graded").count()
    print(u.code, num)  # noqa: T201
