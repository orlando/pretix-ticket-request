from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from pretix.base.models import Event
from pretix.control.views.event import (
    EventSettingsFormView, EventSettingsViewMixin,
)
from pretix.presale.utils import event_view

from .forms import TicketRequestsSettingsForm


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = TicketRequestsSettingsForm
    template_name = 'pretix_ticket_request/settings.html'
    permission = 'can_change_settings'

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
