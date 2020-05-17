from django import template


register = template.Library()


@register.inclusion_tag('academy/grade.html', takes_context=True)
def show_grade(context, grade):
    return {'grade': grade, 'user': context["user"]}
