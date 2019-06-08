from django.conf import settings
from django.urls import include, path, reverse_lazy
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView
from django.views import defaults as default_views
from allauth.account import views

urlpatterns = [
    # path("",
    #      TemplateView.as_view(template_name="pages/home.html"),
    #      name="home"),
    # path("about/",
    #      TemplateView.as_view(template_name="pages/about.html"),
    #      name="about",
    # ),
    path("",
         RedirectView.as_view(url=reverse_lazy('academy:unit-list')),
         name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    path(
        "users/",
        include("portal.users.urls", namespace="users"),
    ),
    # Your stuff: custom urls includes go here
    path("academy/", include("academy.urls")),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

# User management
# TODO sorry, just needed this to work
if settings.LOGIN_URL == 'account_login':
    urlpatterns += [
        path(r"^signup/$", views.signup, name="account_signup"),
        path(r"^login/$", views.login, name="account_login"),
    ]
else:
    urlpatterns += [
        path("accounts/",
             include("allauth.socialaccount.providers.github.urls")),
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
