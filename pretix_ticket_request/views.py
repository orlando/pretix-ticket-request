import pytz

from decimal import Decimal
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import (TemplateView, ListView, FormView, UpdateView)
from django.db import transaction
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

    def get_success_url(self):
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


class TicketRequestUpdate(EventPermissionRequiredMixin, UpdateView):
    form_class = forms.TicketRequestForm
    model = TicketRequest
    template_name = 'pretix_ticket_request/detail.html'
    permission = 'can_change_event_settings'
    context_object_name = 'ticket_request'

    def get_object(self, queryset=None):
        url = resolve(self.request.path_info)
        try:
            return self.request.event.ticket_requests.get(id=url.kwargs['ticket_request'])
        except TicketRequest.DoesNotExist:
            raise Http404(_("The requested ticket request does not exist."))

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _('Your changes have been saved.'))
        if form.has_changed():
            self.object.log_action(
                'pretix.ticket_request.changed', user=self.request.user, data={
                    k: form.cleaned_data.get(k) for k in form.changed_data
                }
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'plugins:pretix_ticket_request:list',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )


class TicketRequestCreate(FormView):
    form_class = forms.TicketRequestForm
    template_name = 'pretix_ticket_request/request.html'

    def get_success_url(self):
        return reverse(
            'plugins:pretix_ticket_request:request',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.event = self.request.event
        form.save()

        messages.success(self.request, _('Your request has been saved. We will email you if you are approved.'))

        return super().form_valid(form)
