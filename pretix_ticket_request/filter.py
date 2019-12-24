from django import forms
from pretix.control.forms.filter import FilterForm
from pretix.base.models import Organizer
from pretix.control.forms.widgets import Select2
from django.urls import reverse, reverse_lazy
from django.utils.translation import pgettext_lazy, ugettext_lazy as _
from .models import TicketRequest


class TicketRequestSearchFilterForm(FilterForm):
    status = forms.ChoiceField(
        label=_('Status'),
        choices=TicketRequest.STATUS_CHOICE,
        required=False
    )

    query = forms.CharField(
        label=_('Search for...'),
        widget=forms.TextInput(attrs={
            'placeholder': _('Event name'),
            'autofocus': 'autofocus'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def filter_qs(self, qs):
        fdata = self.cleaned_data
        qs = super().filter_qs(qs)

        if fdata.get('organizer'):
            qs = qs.filter(event__organizer=fdata.get('organizer'))

        return qs
