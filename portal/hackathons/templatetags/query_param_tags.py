from django import template  # noqa: D100

register = template.Library()


@register.simple_tag(takes_context=True)
def add_query_param(context, field_name, value):  # noqa: ANN001, ANN201, D103
    params = context.request.GET.copy()
    params[field_name] = value

    return f"?{params.urlencode()}" if params else ""