import os

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from sharky.mixins import UUIDPrimaryKeyMixin


def get_placeholder_url(request=None) -> str:
    """
    Return a URL for the placeholder profile image, typically used when
    no custom image exists for a user.

    If a request object is provided, it will be used to construct an
    absolute URL; if no request passed, an absolute URL is constructed
    via settings.SITE_DOMAIN and settings.SITE_SCHEMA if possible.
    If all else fails, then a relative URL is returned.
    """
    url = f'{settings.STATIC_URL}accounts/images/placeholder_profile.png'
    if request:
        return '{}://{}{}'.format(request.scheme, request.get_host(), url)
    elif getattr(settings, 'SITE_DOMAIN', None):
        return '{schema}://{domain}{path}'.format(
            schema=getattr(settings, 'SITE_SCHEMA', 'http'),
            domain=settings.SITE_DOMAIN,
            path=url,
        )
    return url


def user_image_upload_to(user, filename: str) -> str:
    """Upload images to a sensible location."""
    ext = os.path.splitext(filename)[-1]
    if filename == 'blob':
        ext = '.png'

    return f'users/{user.email}/profile{ext}'


class EmailUserManager(BaseUserManager):
    def _create_user(self, email, password=None, is_superuser=False, **kwargs):
        user = self.model(email=email, is_superuser=is_superuser, **kwargs)
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **kwargs):
        return self._create_user(email, password, is_superuser=False, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        return self._create_user(email, password, is_superuser=True, **kwargs)


class EmailUser(AbstractBaseUser, PermissionsMixin, UUIDPrimaryKeyMixin):

    # User information
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    image = models.ImageField(
        upload_to=user_image_upload_to, blank=True, null=True)
    phone = models.CharField(
        max_length=16, blank=True, verbose_name='Phone number')

    # Permissions
    is_developer = models.BooleanField(
        default=False, verbose_name='Developer',
        help_text='User can see developer settings on the frontend clients.')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    objects = EmailUserManager()

    # Core Django Functionality
    def get_full_name(self) -> str:
        """Returns first_name plus last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        """Returns the short name for the User."""
        return self.first_name or self.email

    def email_user(self,
                   subject: str,
                   message: str,
                   from_email: str = None,
                   **kwargs) -> None:
        """Sends an email to this User."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_staff(self) -> bool:
        return self.is_superuser

    def _send_html_mail(self,
                        subject: str,
                        template_html: str,
                        template_text: str,
                        **context) -> None:
        """
        Renders templates to context, and uses EmailMultiAlternatives to
        send email.
        """
        if not template_html:
            raise ValueError('No HTML template provided for email.')
        if not template_text:
            raise ValueError('No text template provided for email.')
        default_context = {
            "settings": settings,
            "user": self
        }
        default_context.update(context)
        from_email = settings.DEFAULT_FROM_EMAIL
        body_text = render_to_string(template_text, default_context)
        body_html = render_to_string(template_html, default_context)

        msg = EmailMultiAlternatives(
            subject=subject, body=body_text,
            from_email=from_email, to=[self.email])
        msg.attach_alternative(body_html, 'text/html')
        msg.send()
