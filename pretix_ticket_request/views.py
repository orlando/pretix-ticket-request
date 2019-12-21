import pytz

from decimal import Decimal
from django import forms
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (TemplateView, ListView, FormView)
from django.db.models import Prefetch
from django.utils.functional import cached_property
from django_countries import countries
from django_countries.fields import Country, CountryField
from phonenumber_field.formfields import PhoneNumberField

from pretix.base.models import (Event, Item, Question)
from pretix.control.views.event import (
    EventSettingsFormView, EventSettingsViewMixin
)
from pretix.control.permissions import EventPermissionRequiredMixin

from . import forms
from .models import TicketRequest


class TicketRequestSettings(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = forms.TicketRequestsSettingsForm
    template_name = 'pretix_ticket_request/settings.html'
    permission = 'can_change_event_settings'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse(
            'plugins:pretix_ticket_request:settings',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )


class TicketRequestList(EventPermissionRequiredMixin, ListView):
    model = TicketRequest
    context_object_name = 'ticket_requests'
    paginate_by = 20
    template_name = 'pretix_ticket_request/index.html'
    permission = 'can_change_event_settings'

    def get_queryset(self):
        return TicketRequest.objects.filter(event=self.request.event)


class TicketRequestCreate(FormView):
    form_class = forms.TicketRequestForm
    template_name = 'pretix_ticket_request/request.html'
