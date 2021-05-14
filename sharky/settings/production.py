"""
Base settings, extended by the dev/staging/production settings.
"""

import os
from django.utils.log import DEFAULT_LOGGING

DEBUG = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))


MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sharky.middleware.GraphQLAuthErrorMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # 3rd party apps
    'django_extensions',
    'corsheaders',
    'graphene_django',
    'graphql_auth',
    'graphql_jwt.refresh_token.apps.RefreshTokenConfig',

    # Local Apps
    'apps.accounts',
    "apps.lending",
)

# Domain configuration
SITE_SCHEMA = os.environ.get('SCHEMA', 'http')
SITE_DOMAIN = os.environ.get('FQDN', 'localhost')
# Retrieve list of space separated domains
# E.G. export ADDITIONAL_DOMAINS='foo.com www.foo.com staging.bar.com'
SITE_DOMAINS = os.environ.get('ADDITIONAL_DOMAINS', '').split()
FRONTEND_OAUTH_REDIRECT = 'http://local.izeni.net:9000/oauth/'

CORS_ORIGIN_ALLOW_ALL = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'sharky'),
        'USER': os.environ.get('DB_USER', 'sharky'),
        'PASSWORD': os.environ.get('DB_PASS', 'sharky'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Auth Configuration
AUTH_USER_MODEL = 'accounts.EmailUser'

AUTHENTICATION_BACKENDS = [
    'graphql_auth.backends.GraphQLAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]


#####################
# GRAPHENE SETTINGS #
#####################
GRAPHENE = {
    'SCHEMA': 'sharky.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}


################################
# DJANGO GRAPHQL AUTH SETTINGS #
################################
GRAPHQL_AUTH = {
    'LOGIN_ALLOWED_FIELDS': ['email'],
    'REGISTER_MUTATION_FIELDS': {
        'email': 'String',
        'first_name': 'String',
        'last_name': 'String',
        'phone': 'String'
    },
    'USER_NODE_FILTER_FIELDS': {
        'email': ['exact'],
        'status__archived': ['exact'],
        'status__verified': ['exact'],
        'status__secondary_email': ['exact'],
    },
    'ACTIVATION_PATH_ON_EMAIL': 'verify-email',
    'PASSWORD_RESET_PATH_ON_EMAIL': 'reset-pass',
    'ALLOW_LOGIN_AFTER_VERIFY': True
}

GRAPHQL_JWT = {
    "JWT_ALLOW_ANY_CLASSES": [
        "graphql_auth.mutations.Register",
        "graphql_auth.mutations.VerifyAccount",
        "graphql_auth.mutations.ResendActivationEmail",
        "graphql_auth.mutations.SendPasswordResetEmail",
        "graphql_auth.mutations.PasswordReset",
        "graphql_auth.mutations.ObtainJSONWebToken",
        "graphql_auth.mutations.VerifyToken",
        "graphql_auth.mutations.RefreshToken",
        "graphql_auth.mutations.RevokeToken",
    ],
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
}


#############################################################################
# You will only rarely need to change anything below here.
#############################################################################


class EmailSettings:
    HEADER_COLOR = "#03a9f4"  # Material Blue 500
    BG_COLOR = "#f5f5f5"  # Material Grey 100
    CONTENT_COLOR = "#ffffff"  # White
    HIGHLIGHT_COLOR = "#f5f5f5"  # Material Grey 100
    LOGO_URL = "http://izeni.com/static/img/izeni-shadow.png"
    LOGO_ALT_TEXT = ""
    TERMS_URL = ""
    PRIVACY_URL = ""
    UNSUBSCRIBE_URL = ""
    FONT_CSS = 'font-family: "Helvetica Neue", "Helvetica", Helvetica, Arial, sans-serif;'
    FONT_CSS_HEADER = 'font-family: "HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif;'


EMAIL = EmailSettings()
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_PORT = os.environ.get('EMAIL_HOST_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = bool(os.environ.get('EMAIL_USE_TLS'))
DEFAULT_FROM_EMAIL = 'admin@{}'.format(SITE_DOMAIN)

# General
MANAGERS = ADMINS = (
    ('sharky Admin', 'sharky+admin@izeni.com'),
)

IZENI = {
    'ADMIN': {
        'SITE_TITLE': "sharky backend",
    }
}

# Host names
INTERNAL_IPS = ('127.0.0.1',)
ALLOWED_HOSTS = [SITE_DOMAIN] + SITE_DOMAINS


# Logging
# The numeric values of logging levels are in the following table:
#
# CRITICAL    50
# ERROR       40
# WARNING     30
# INFO        20
# DEBUG       10
# NOTSET      0 [default]
#
# Messages which are less severe than the specified level will be ignored.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': DEFAULT_LOGGING['filters'],
    'formatters': {
        'default': {
            '()': 'logging.Formatter',
            'format': '[%(asctime)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'debug': {
            '()': 'logging.Formatter',
            'format': '[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': ['require_debug_false'],
        },
        'debug-console': {
            'level': 'INFO',  # DEBUG level here is *extremely* noisy
            'class': 'logging.StreamHandler',
            'formatter': 'debug',
            'filters': ['require_debug_true'],
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': '/var/log/sharky/django.log',
            'maxBytes': 1000000,  # 1MB
            'delay': True,
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'debug-console', 'file'],
            'level': 'NOTSET',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'debug-console', 'file'],
            'level': 'NOTSET',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'debug-console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


# Caching
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}


# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'sharky', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# password policies
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


#############################################################################
# You shouldn't ever have to change anything below here.
#############################################################################


# Static/Media
MEDIA_ROOT = '/var/media/sharky/media'
MEDIA_URL = '/media/'
STATIC_ROOT = '/var/media/sharky/static'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'sharky', 'static'),
)


# URLs
ROOT_URLCONF = 'sharky.urls'


# ./manage.py runserver WSGI configuration
WSGI_APPLICATION = 'sharky.wsgi.application'


# i18n
USE_TZ = True
TIME_ZONE = 'Asia/Manila'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True


# Secrets
SECRET_KEY = 'django-insecure-=*h23yiw&t2s4@xk=(^s3wf$5dm_a8g=ikp3($8=23zt)6kbx5'
