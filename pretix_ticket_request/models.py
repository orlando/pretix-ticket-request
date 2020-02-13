from django.core.validators import RegexValidator
from django.db import models, transaction
from django_countries.fields import Country
from django.utils.translation import (
    pgettext_lazy, ugettext_lazy as _, ugettext_noop,
)
from jsonfallback.fields import FallbackJSONField
from i18nfield.fields import I18nCharField, I18nTextField
from i18nfield.strings import LazyI18nString

from pretix.base.models import (LoggedModel, Voucher)
from pretix.base.i18n import language
from pretix.base.email import get_email_context
from pretix.base.services.mail import mail
from pretix.multidomain.urlreverse import build_absolute_uri


class TicketRequest(LoggedModel):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_CHOICE = (
        (STATUS_PENDING, _("pending")),
        (STATUS_APPROVED, _("paid")),
        (STATUS_REJECTED, _("expired")),
        (STATUS_WITHDRAWN, _("withdrawn")),
    )

    event = models.ForeignKey('pretixbase.Event', on_delete=models.CASCADE, related_name="ticket_requests")
    voucher = models.ForeignKey(
        'pretixbase.Voucher',
        verbose_name=_("Assigned voucher"),
        null=True, blank=True,
        related_name='ticket_request',
        on_delete=models.PROTECT
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Full name"),
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        null=False,
        blank=False,
        verbose_name=_('E-mail'),
        max_length=190
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICE,
        verbose_name=_("Status"),
        db_index=True,
        default=STATUS_PENDING
    )
    data = FallbackJSONField(
        blank=True, default=dict
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def approved(self):
        return self.status == self.STATUS_APPROVED

    def approve(self, user=None):
        # return if status is not equal to 'pending'
        if self.status != TicketRequest.STATUS_PENDING:
            return False

        # set status to approved if ticket request has a voucher assigned
        if self.voucher:
            self.status = TicketRequest.STATUS_APPROVED
            self.save()
            return False

        self.status = TicketRequest.STATUS_APPROVED
        self.send_voucher(self, user=user)

    def reject(self, user=None):
        if self.status != TicketRequest.STATUS_PENDING:
            return False

        self.status = TicketRequest.STATUS_REJECTED
        self.log_action('pretix.ticket_request.rejected', user=user)
        self.save()

    @property
    def country(self):
        return Country(code=self.data.get('country'))

    def send_voucher(self, quota_cache=None, user=None):
        event = self.event
        quota_id = event.settings.ticket_request_quota
        quota = event.quotas.get(id=quota_id)
        locale = 'en'

        with transaction.atomic():
            v = Voucher.objects.create(
                event=event,
                max_usages=1,
                quota=quota,
                tag='ticket-request',
                valid_until=event.date_to,
                comment=_('Automatically created from ticket request entry for {email}').format(
                    email=self.email
                ),
                block_quota=True,
            )
            v.log_action('pretix.voucher.approved.ticket_request', {
                'quota': quota,
                'tag': 'ticket-request',
                'block_quota': True,
                'valid_until': v.valid_until.isoformat(),
                'max_usages': 1,
                'email': self.email,
            }, user=user)
            self.log_action('pretix.ticket_request.approved', user=user)
            self.voucher = v
            self.save()

        with language(locale):
            email_content = LazyI18nString.from_gettext(ugettext_noop("""Congratulations!! You just got approved for an IFF Ticket. You can redeem it in our ticket shop by entering the following voucher code following the directions listed below:

{code}

Alternatively, you can just click on the following link:

<a href="{url}">{url}</a>

If you need a visa for the event, please fill out this form as soon as possible, and someone will get back to you <a href="https://internetfreedomfestival.formstack.com/forms/iff2020_visa">https://internetfreedomfestival.formstack.com/forms/iff2020_visa</a>

We look forward to seeing you soon! If you have any questions, don’t hesitate to reach out to <a href="mailto:team@internetfreedomfestival.org">team@internetfreedomfestival.org</a>. We look forward to seeing you at the IFF!

The IFF Team.<br /><br />

<h3>DIRECTIONS TO CLAIM YOUR TICKET</h3>

<ol>
  <li>Visit: <a href="https://tickets.internetfreedomfestival.org/iff/2020/">https://tickets.internetfreedomfestival.org/iff/2020/</a></li>
  <li>Input your voucher code listed above into the section “Redeem a
voucher” and press “REDEEM VOUCHER”</li>
  <li>
    On the next page, select the ticket type you would like by checking
    ONLY ONE of the three checkboxes listed, and then press “PROCEED TO
    CHECKOUT”.<br /><br />

    ---> Tickets to the IFF are free but if you are considering donating,
please select “Supporter Ticket” and include the amount you want to pay,
or select “Organizational Ticket” which has a set rate.<br /><br />

<b>Please Note * If you pick more than one ticket type, your order
may be canceled.</b>
  </li>
  <li>
  Review your order and press “PROCEED WITH CHECKOUT”.<br /><br />

  <b>Please Note * If you select the wrong ticket type, you can restart
the process by clicking the back button on your browser.</b>
  </li>
  <li>
On the next page, please add your email to both boxes listed under
“Contact Information” and press ”CONTINUE”
  </li>
  <li>
An email from “team@internetfreedomfestival.org” will be sent to you
with a verification code, which you must insert in the following page in
the box labeled “VERIFICATION CODE”
  </li>
  <li>
On the “Your Profile” page, you must fill out your personal
information and press “CONTINUE”
  </li>
  <li>
You will have a chance to review your order once more. If everything
is correct, press “SUBMIT REGISTRATION”
  </li>
  <li>
On the final page, you can download the PDF of your ticket.   You
will need this PDF to enter the IFF. Note, the system will also send you
an email with a PDF, a link to your ticket, as well as your unique
ticket code.
  </li>
</ol>

"""))

            email_context = {
                'event': event,
                'url': build_absolute_uri(
                    event, 'presale:event.redeem'
                ) + '?voucher=' + self.voucher.code,
                'code': self.voucher.code
            }

            mail(
                self.email,
                _('Claim your IFF Ticket!!').format(event=str(event)),
                email_content,
                email_context,
                event,
                locale=locale
            )

    class Meta:
        ordering = ['created_at', 'status']


class Attendee(LoggedModel):
    event = models.ForeignKey('pretixbase.Event', on_delete=models.CASCADE, related_name="attendees")
    verified = models.BooleanField(default=False)
    email = models.EmailField(
        unique=True,
        db_index=True,
        null=False,
        blank=False,
        verbose_name=_('E-mail'),
        max_length=190
    )
    profile = FallbackJSONField(
        blank=True, default=dict
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def has_profile(self):
        return self.profile
