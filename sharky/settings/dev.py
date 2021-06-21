"""
Development settings, extends the base settings.
"""
from .production import *

DEBUG = True
SITE_DOMAIN = "localhost:8000"  # should not have a trailing slash
MEDIA_ROOT = os.path.join(BASE_DIR, "server", "dev", "media")
STATIC_ROOT = os.path.join(BASE_DIR, "server", "dev", "static")
AUTH_PASSWORD_VALIDATORS = []  # disable password policies
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
