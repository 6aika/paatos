import os

from django.utils.translation import ugettext_lazy as _
from environ import Env

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
assert os.path.exists(os.path.join(BASE_DIR, "manage.py"))

env = Env()

DEBUG = env.bool('DEBUG', default=False)
LANGUAGE_CODE = "fi"
LANGUAGES = [
    ('fi', _('Finnish')),
    ('sv', _('Swedish')),
    ('en', _('English'))
]
VAR_ROOT = env.str("VAR_ROOT", default=BASE_DIR)
if not os.path.isdir(VAR_ROOT):
    os.makedirs(VAR_ROOT)
MEDIA_ROOT = os.path.join(VAR_ROOT, "media")
MEDIA_URL = "/media/"
ROOT_URLCONF = "paatos.urls"
STATIC_ROOT = env.str('STATIC_ROOT', default=os.path.join(VAR_ROOT, "static"))
STATIC_URL = "/static/"
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True
WSGI_APPLICATION = "paatos.wsgi.application"


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "easy_select2",
    "rest_framework_gis",
    "paatos",
    "decisions",
]

MIDDLEWARE_CLASSES = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'db',
        'PORT': '5432',
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'decisions.importer': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_PERMISSION_CLASS': 'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

OPEN_AHJO_ATTACHMENT_URL_BASE = 'https://dev.hel.fi/paatokset'


# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
f = os.path.join(BASE_DIR, "local_settings.py")
if os.path.exists(f):
    import sys
    import imp
    module_name = "%s.local_settings" % ROOT_URLCONF.split('.')[0]
    module = imp.new_module(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    exec(open(f, "rb").read())

if 'SECRET_KEY' not in locals():
    secret_file = os.path.join(BASE_DIR, '.django_secret')
    try:
        SECRET_KEY = open(secret_file).read().strip()
    except IOError:
        import random
        system_random = random.SystemRandom()
        try:
            CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            SECRET_KEY = ''.join([system_random.choice(CHARS) for i in range(64)])
            secret = open(secret_file, 'w')
            import os
            os.chmod(secret_file, 0o0600)
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters to generate your secret key!' % secret_file)
