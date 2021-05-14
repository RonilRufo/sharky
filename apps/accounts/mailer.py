from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _


User = get_user_model()


class AccountsMailer():

    subjects = {
        'existing_email': _("sharky: Email used in signup")
    }

    def send(self,
             subject: str,
             template: str,
             context: dict,
             recipient_list: List[str]):
        """
        Generic method for sending email.
        """
        html_message = render_to_string(template, context)
        message = strip_tags(html_message)

        return send_mail(
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            message=message,
            html_message=html_message,
            recipient_list=recipient_list,
            fail_silently=False
        )

    def send_existing_email(self, **context):
        subject = self.subjects['existing_email']
        template = "accounts/email/email_existing.html"
        recipient = context.get(User.USERNAME_FIELD)
        return self.send(subject, template, context, [recipient])
