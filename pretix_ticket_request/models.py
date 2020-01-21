from django.core.validators import RegexValidator
from django.db import models, transaction
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
        if self.status != TicketRequest.STATUS_PENDING:
            return False

        self.status = TicketRequest.STATUS_APPROVED
        self.send_voucher(self, user=user)

    def reject(self, user=None):
        if self.status != TicketRequest.STATUS_PENDING:
            return False

        self.status = TicketRequest.STATUS_REJECTED
        self.log_action('pretix.ticket_request.rejected', user=user)
        self.save()

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
            email_content = LazyI18nString.from_gettext(ugettext_noop("""Hello,

We now have a ticket ready for you! You can redeem it in our ticket shop
by entering the following voucher code:

{code}

Alternatively, you can just click on the following link:

<a href="{url}">{url}</a>

Best regards,
Your {event} team"""))

            email_context = {
                'event': event,
                'url': build_absolute_uri(
                    event, 'presale:event.redeem'
                ) + '?voucher=' + self.voucher.code,
                'code': self.voucher.code
            }

            mail(
                self.email,
                _('You have been selected for {event}').format(event=str(event)),
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
