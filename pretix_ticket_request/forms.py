import json

from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from i18nfield.forms import (
    I18nForm, I18nFormField, I18nTextarea, I18nTextInput,
)
from pretix.base.forms import SettingsForm
from pretix.base.forms.widgets import DatePickerWidget
from pretix.base.models import (Item, Quota)


class TicketRequestsSettingsForm(I18nForm, SettingsForm):
    ticket_request_item = forms.ModelChoiceField(
        label='Ticket',
        queryset=Item.objects.none(),
        required=False,
        empty_label='Choose a Ticket',
        help_text="We will render the questions assigned to this Ticket in the Form"
    )

    ticket_request_quota = forms.ModelChoiceField(
        label='Ticket Quota',
        queryset=Quota.objects.none(),
        required=False,
        empty_label='Choose a Quota',
        help_text="Voucher will be created for any ticket under this quota"
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        # Load tickets
        self.fields['ticket_request_item'].queryset = Item.objects.filter(event=self.event)

        # Load quotas
        self.fields['ticket_request_quota'].queryset = Quota.objects.filter(event=self.event)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
