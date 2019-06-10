from django import template


register = template.Library()


@register.inclusion_tag('academy/grade.html')
def show_grade(grade):
    return {'grade': grade}
