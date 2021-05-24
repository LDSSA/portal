from django.conf import settings

from portal.admissions import domain


def admissions_context_processor(request):
    my_dict = {
        'ADMISSIONS_ENABLED': settings.ADMISSIONS_ENABLED,
        'ADMISSIONS_OPEN': domain.admissions_open(),
        'ADMISSIONS_ENDED': domain.admissions_ended(),
    }

    return my_dict