import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sharky.settings.dev")

application = get_wsgi_application()

# log and raise an exception if email settings aren't configured in production
if not settings.DEBUG and not settings.EMAIL_HOST:
    import logging

    logger = logging.getLogger("wsgi")
    logger.critical("Email settings appear to be invalid. Please check them!")
    raise ImproperlyConfigured("settings.EMAIL_HOST not set!")
