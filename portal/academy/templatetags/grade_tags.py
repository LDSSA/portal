from django import template  # noqa: D100

register = template.Library()


@register.inclusion_tag("academy/grade.html", takes_context=True)
def show_grade(context, grade):  # noqa: ANN001, ANN201, D103
    return {"grade": grade, "user": context["user"]}
