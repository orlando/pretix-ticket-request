from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (TemplateView, ListView)
from pretix.base.models import Event
from pretix.base.forms import I18nModelForm
from pretix.control.views.event import (
    EventSettingsFormView, EventSettingsViewMixin, CreateView
)
from pretix.control.permissions import EventPermissionRequiredMixin, event_permission_required
from pretix.presale.utils import event_view

from .forms import TicketRequestsSettingsForm
from .models import TicketRequest


class TicketRequestSettings(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = TicketRequestsSettingsForm
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


class TicketRequestForm(I18nModelForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs.get('event')
        super().__init__(*args, **kwargs)

    class Meta:
        model = TicketRequest
        fields = (
            'email',
        )


class TicketRequestCreate(CreateView):
    model = TicketRequest
    form_class = TicketRequestForm
    template_name = 'pretix_ticket_request/form.html'
    permission = 'can_change_event_settings'

    def get_queryset(self):
        return TicketRequest.objects.filter(event=self.request.event)
