from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def add_query_param(context, field_name, value):
    params = context.request.GET.copy()
    params[field_name] = value

    return f"?{params.urlencode()}" if params else ""
