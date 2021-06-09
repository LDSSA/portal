from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from allauth.account import views

from portal.academy.views import HomeRedirectView

urlpatterns = [
    # General
    path("accounts/", include("allauth.urls")),
    # path("accounts/instructor/signup", include("")),  # TODO LDSSA/portal#98
    # path("",
    #      TemplateView.as_view(template_name="pages/home.html"),
    #      name="home"),
    # path("about/",
    #      TemplateView.as_view(template_name="pages/about.html"),
    #      name="about",
    # ),
    path("", HomeRedirectView.as_view(), name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    path(
        "users/",
        include("portal.users.urls", namespace="users"),
    ),
    # Admissions
    path("admissions/", include("admissions.urls")),
    # Academy
    path("academy/", include("academy.urls")),
    path("hackathons/", include("hackathons.urls")),
    path("capstone/", include("capstone.urls")),
    # Grading
    path("grading/", include("grading.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns
