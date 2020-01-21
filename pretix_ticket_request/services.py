from random import randint
from django.utils.translation import (
    pgettext_lazy, ugettext_lazy as _, ugettext_noop,
)

from i18nfield.strings import LazyI18nString

from pretix.base.i18n import language
from pretix.base.email import get_email_context
from pretix.base.services.mail import mail


class VerificationCodeMailer:
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.email = kwargs.pop('email')

        super().__init__(*args, **kwargs)

    def send(self):
        """
        Mail the generated random 6 digit string of numbers to user's email address
        """
        # Generate the verification code and save it
        self._generate_code()
        self._mail()

    def _generate_code(self):
        """
        Generate a random 6 digit string of numbers.
        We use this formatting to allow leading 0s.
        """
        self.code = str("%06d" % randint(0, 999999))
        return self.code

    def _mail(self):
        # Mail the code to self.email
        # return the verification code
        # code will be stored in the session by the view
        locale = 'en'
        with language(locale):
            email_content = LazyI18nString.from_gettext(ugettext_noop("""Hello,

Here's your verification code. Use it to validate your email and continue the checkout process.

<strong>{code}</strong>

Best regards,
Your {event} team"""))

        email_context = {
            'event': self.event,
            'code': self.code
        }

        mail(
            self.email,
            _("Here's your verification code for {event}").format(event=str(self.event)),
            email_content,
            email_context,
            self.event,
            locale=locale
        )
