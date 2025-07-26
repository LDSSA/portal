"""Base settings to build other settings files upon."""

import os
from datetime import datetime, timedelta, timezone

import environ

ROOT_DIR = environ.Path(__file__) - 3  # (portal/config/settings/base.py - 3 = portal/)
APPS_DIR = ROOT_DIR.path("portal")

env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR.path(".env")))

# CAPSTONE
# ------------------------------------------------------------------------------
TIMEOUT = 5
SIMULATOR_INTERVAL = 5
PRODUCER_INTERVAL = 1

# GRADING
# ------------------------------------------------------------------------------
GRADING_USERNAME = env.str("GRADING_USERNAME")
GRADING_CLASS = env.str(
    "GRADING_CLASS", default="portal.grading.services.AcademyKubernetesGrading"
)
GRADING_ADMISSIONS_CLASS = env.str(
    "GRADING_ADMISSIONS_CLASS",
    default="portal.grading.services.AdmissionsKubernetesGrading",
)
BASE_URL = f'https://{env.str("BASE_URL")}'
STUDENT_REPO_NAME = env.str("STUDENT_REPO_NAME")
IN_DEV = True if "dev" in BASE_URL else False

# ADMISSIONS
# ------------------------------------------------------------------------------

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings
DEBUG = env.bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = False
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

DATETIME_FORMAT = "Y-m-d H:i:s e"
DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i:s e"
SHORT_DATETIME_FORMAT = "Y-m-d H:i:s e"

# DATABASES
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    },
}

# CACHES
# ------------------------------------------------------------------------------
CACHE_BACKEND = env(
    "DJANGO_CACHE_BACKEND",
    default="django.core.cache.backends.locmem.LocMemCache",
)

if CACHE_BACKEND == "django.core.cache.backends.locmem.LocMemCache":
    # https://docs.djangoproject.com/en/dev/ref/settings/#caches
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "",
        },
    }
elif CACHE_BACKEND == "django_redis.cache.RedisCache":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicking memcache behavior.
                # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
                "IGNORE_EXCEPTIONS": True,
            },
        },
    }

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 'django.contrib.humanize', # Handy template tags
    "django.contrib.admin",
]
THIRD_PARTY_APPS = [
    "constance",
    "constance.backends.database",
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_framework",
    "rest_framework.authtoken",
    "crispy_bootstrap4",
]
LOCAL_APPS = [
    "portal.users.apps.UsersAppConfig",
    "portal.academy.apps.AcademyConfig",
    "portal.hackathons.apps.HackathonsConfig",
    "portal.capstone.apps.CapstoneConfig",
    "portal.admissions.apps.AdmissionsConfig",
    "portal.applications.apps.ApplicationsConfig",
    "portal.candidate.apps.CandidateConfig",
    "portal.staff.apps.StaffConfig",
    "portal.selection.apps.SelectionConfig",
    "portal.grading.apps.GradingConfig",
    "portal.scheduler.apps.SchedulerConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "portal.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "home"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = env.str("DJANGO_LOGIN_URL", "account_login")

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# STORAGES
# ------------------------------------------------------------------------------
STATICFILES_STORAGE = env(
    "DJANGO_STATICFILES_STORAGE",
    default="django.contrib.staticfiles.storage.StaticFilesStorage",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR("staticfiles"))
STATICFILES_DIRS = [
    str(APPS_DIR.path("static")),
]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

if STATICFILES_STORAGE == "config.settings.settings.StaticRootS3Boto3Storage":
    AWS_DEFAULT_ACL = None
    # https://django-storages.readthedocs.io/en/latest/#installation
    INSTALLED_APPS += ["storages"]
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_QUERYSTRING_AUTH = False
    # DO NOT change these unless you know what you're doing.
    _AWS_EXPIRY = 60 * 60 * 24 * 7
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate",
    }
    AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

    STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/"

    # region http://stackoverflow.com/questions/10390244/
    # Full-fledge class: https://stackoverflow.com/a/18046120/104731
    from storages.backends.s3boto3 import S3Boto3Storage

    class StaticRootS3Boto3Storage(S3Boto3Storage):
        location = "static"

    class MediaRootS3Boto3Storage(S3Boto3Storage):
        location = "media"
        file_overwrite = False

    # endregion
    DEFAULT_FILE_STORAGE = "config.settings.settings.MediaRootS3Boto3Storage"
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/"

elif STATICFILES_STORAGE == "django.contrib.staticfiles.storage.StaticFilesStorage":
    # https://docs.djangoproject.com/en/dev/ref/settings/#static-url
    STATIC_URL = "/static/"
    # https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
    STATICFILES_DIRS = [
        str(APPS_DIR.path("static")),
    ]
    # https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
    STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    ]

    # https://docs.djangoproject.com/en/dev/ref/settings/#media-root
    MEDIA_ROOT = str(APPS_DIR("media"))
    # https://docs.djangoproject.com/en/dev/ref/settings/#media-url
    MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [
            str(APPS_DIR.path("templates")),
        ],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": DEBUG,
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "portal.admissions.context_processors.admissions_context_processor",
                # 'portal.users.context_processors.login_view',
            ],
        },
    },
]
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

CACHE_TEMPLATES = env.bool("DJANGO_CACHE_TEMPLATES", default=True)
if CACHE_TEMPLATES:
    # https://docs.djangoproject.com/en/dev/ref/settings/#templates
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

SECURITY_EXTRAS = env.bool("DJANGO_SECURITY_EXTRAS", default=True)
if SECURITY_EXTRAS:
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    # https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
    SESSION_COOKIE_SECURE = True
    # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
    CSRF_COOKIE_SECURE = True
    # https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
    # TODO: set this to 60 seconds first and then to 518400 once you prove the former works
    SECURE_HSTS_SECONDS = 60
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
    )
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
    SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
    # https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
    SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
        "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
    )

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="notifications@lisbondatascience.org"
)
ADMISSIONS_FROM_EMAIL = env(
    "ADMISSIONS_FROM_EMAIL", default="admissions@lisbondatascience.org"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[LDSSA Portal]")

if EMAIL_BACKEND in (
    "django.core.mail.backends.smtp.EmailBackend",
    "portal.anymail_elasticmail.smtp.PortalEmailBackend",
):
    if DEBUG:
        # https://docs.djangoproject.com/en/dev/ref/settings/#email-host
        EMAIL_HOST = env("EMAIL_HOST", default="mailhog")
        # https://docs.djangoproject.com/en/dev/ref/settings/#email-port
        EMAIL_PORT = 1025

    else:
        EMAIL_HOST = env("DJANGO_EMAIL_HOST")
        EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD")
        EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER")
        EMAIL_PORT = env("DJANGO_EMAIL_PORT")
        EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_PORT")

elif EMAIL_BACKEND == "portal.anymail_elasticmail.elasticmail.ElasticmailBackend":
    ANYMAIL = {
        "ELASTICMAIL_API_KEY": env("ELASTICMAIL_API_KEY"),
    }


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL base
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("Hugo Castilho", "hcastilho@lisbondatascience.org"),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# crispy forms
# ------------------------------------------------------------------------------
CRISPY_TEMPLATE_PACK = "bootstrap4"


# django-constance
# ------------------------------------------------------------------------------
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
# CONSTANCE_DATABASE_CACHE_BACKEND ='default'
#
# * Admissions                    
#   - Sign up                     -> admissions
#   - Applications                -> admissions:applications
#     - CoC
#     - Scholarship
#     - Challenge/Submissions
#   - Selection                   -> admissions:selection
# * Academy                       -> academy
#
CONSTANCE_CONFIG = {
    # Portal config
    "ACCOUNT_ALLOW_REGISTRATION": (True, "Allow Sign Ups"),  # Allow sign ups
    "PORTAL_STATUS": (
        "admissions:applications",
        "One of: admissions, admissions:applications, admissions:selection, academy",
    ),
    # Academy config
    "ACADEMY_START": (datetime.now(timezone.utc), ""),
    # Admissions config
    "ADMISSIONS_CODING_TEST_DURATION": (timedelta(hours=3), ""),
    "ADMISSIONS_APPLICATIONS_START": (datetime.now(timezone.utc), ""),
    "ADMISSIONS_SELECTION_START": (datetime.now(timezone.utc), ""),
    "ADMISSIONS_ACCEPTING_PAYMENT_PROFS": (True, ""),
}
ADMISSIONS_APPLICATIONS_STARTED_STATUSES = [
    "admissions:applications",
    "admissions:selection",
]


# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "portal.users.adapters.AccountAdapter"
# SOCIALACCOUNT_ADAPTER = "portal.users.adapters.SocialAccountAdapter"
ACCOUNT_SIGNUP_FORM_CLASS = "portal.users.forms.PortalSignupForm"


# django-compressor
# ------------------------------------------------------------------------------
# https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_ENABLED
COMPRESS_ENABLED = env.bool("COMPRESS_ENABLED", default=True)
if COMPRESS_ENABLED:
    # https://django-compressor.readthedocs.io/en/latest/quickstart/#installation
    INSTALLED_APPS += ["compressor"]
    try:
        STATICFILES_FINDERS += ["compressor.finders.CompressorFinder"]
    except NameError:
        STATICFILES_FINDERS = ["compressor.finders.CompressorFinder"]

    # https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_STORAGE
    COMPRESS_STORAGE = env(
        "COMPRESS_STORAGE", default="compressor.storage.CompressorFileStorage"
    )
    # https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_URL
    COMPRESS_URL = STATIC_URL


# django-rest-framework
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAdminUser",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

# django-debug-toolbar
# ------------------------------------------------------------------------------
if DEBUG:
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
    INSTALLED_APPS += ["debug_toolbar"]
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": [
            "debug_toolbar.panels.redirects.RedirectsPanel",
        ],
        "SHOW_TEMPLATE_CONTEXT": True,
    }
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
    if env("USE_DOCKER") == "yes":
        import socket

        hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
        INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
if DEBUG:
    INSTALLED_APPS += ["django_extensions"]

# Gunicorn
# ------------------------------------------------------------------------------
GUNICORN_ENABLED = env.bool("GUNICORN_ENABLED", default=True)
if GUNICORN_ENABLED:
    INSTALLED_APPS += ["gunicorn"]


# Collectfast
# ------------------------------------------------------------------------------
# https://github.com/antonagestam/collectfast#installation
if STATICFILES_STORAGE == "storages.backends.s3boto.S3BotoStorage":
    INSTALLED_APPS = ["collectfast", *INSTALLED_APPS]
    AWS_PRELOAD_METADATA = True

# Sentry
# ------------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.005,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(name)s.%(funcName)s/%(lineno)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "parso": {
            "level": "WARNING",
        },
        "botocore": {
            "level": "WARNING",
        },
        "urllib3": {
            "level": "WARNING",
        },
        "s3transfer": {
            "level": "WARNING",
        },
    },
}

# SLACK
# ------------------------------------------------------------------------------
SLACK_WORKSPACE = env.str("SLACK_WORKSPACE")
