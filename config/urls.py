from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from allauth.account import views

from portal.academy.views import HomeRedirectView

urlpatterns = [
    # path("",
    #      TemplateView.as_view(template_name="pages/home.html"),
    #      name="home"),
    # path("about/",
    #      TemplateView.as_view(template_name="pages/about.html"),
    #      name="about",
    # ),
    path("",
         HomeRedirectView.as_view(),
         name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    path(
        "users/",
        include("portal.users.urls", namespace="users"),
    ),
    # Your stuff: custom urls includes go here
    path("academy/", include("academy.urls")),
    path("hackathons/", include("hackathons.urls")),
    path("capstone/", include("capstone.urls")),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

# User management
urlpatterns += [
    path("signup/", views.signup, name="account_signup"),
    path("login/", views.login, name="account_login"),
    path("logout/", views.logout, name="account_logout"),
    # password reset
    path("password/reset/",
            views.password_reset,
            name="account_reset_password"),
    path("password/reset/done/",
            views.password_reset_done,
            name="account_reset_password_done"),
    re_path(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
            views.password_reset_from_key,
            name="account_reset_password_from_key"),
    path("password/reset/key/done/",
            views.password_reset_from_key_done,
            name="account_reset_password_from_key_done"),
]

urlpatterns += [
    path(r"accounts/email/", views.email, name="account_email"),
]


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

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
