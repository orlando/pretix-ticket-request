from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from i18nfield.fields import I18nCharField, I18nTextField
from pretix.base.models import LoggedModel


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

    event = models.ForeignKey('pretixbase.Event', on_delete=models.CASCADE)
    waiting_list_entry = models.ForeignKey('pretixbase.WaitingListEntry', on_delete=models.PROTECT)
    email = models.EmailField(unique=True, db_index=True, null=False, blank=False,
                              verbose_name=_('E-mail'), max_length=190)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICE,
        verbose_name=_("Status"),
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'status']


class TicketRequestAnswer(LoggedModel):
    ticket_request = models.ForeignKey('pretix_ticket_request.TicketRequest', on_delete=models.CASCADE)
    question = models.ForeignKey('pretixbase.Question', on_delete=models.PROTECT)
    answer = models.TextField()
