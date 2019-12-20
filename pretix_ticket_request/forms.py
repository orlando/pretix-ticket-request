import json
import pdb

from django import forms
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from i18nfield.forms import (
    I18nForm, I18nFormField, I18nTextarea, I18nTextInput,
)
from pretix.base.forms import SettingsForm
from pretix.base.forms.widgets import DatePickerWidget
from pretix.base.models import Item


class TicketRequestsSettingsForm(I18nForm, SettingsForm):
    # General settings
    ticket_request_item = forms.ModelChoiceField(
        label='Ticket',
        queryset=Item.objects.none(),
        required=False,
        empty_label='Choose a Ticket'
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

        # Load tickets
        self.fields['ticket_request_item'].queryset = Item.objects.filter(event=self.event)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
