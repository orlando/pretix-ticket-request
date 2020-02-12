import pytz

from decimal import Decimal
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.core.validators import EmailValidator
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import (TemplateView, ListView, FormView, UpdateView)
from django.db import transaction
from django.utils.functional import cached_property

from pretix.base.models import (Event, Item, Question)
from pretix.control.views.event import (
    EventSettingsFormView, EventSettingsViewMixin, PaginationMixin
)
from pretix.control.permissions import (
    EventPermissionRequiredMixin,
    event_permission_required
)
from pretix.presale.views import CartMixin
from pretix.presale.checkoutflow import TemplateFlowStep

from . import forms
from .services import VerificationCodeMailer
from .models import (TicketRequest, Attendee)
from .filter import TicketRequestSearchFilterForm


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


class TicketRequestList(EventPermissionRequiredMixin, PaginationMixin, ListView):
    model = TicketRequest
    context_object_name = 'ticket_requests'
    paginate_by = 20
    template_name = 'pretix_ticket_request/index.html'
    permission = 'can_change_event_settings'

    def get_queryset(self):
        qs = TicketRequest.objects.filter(
            event=self.request.event
        ).select_related('voucher')

        if self.filter_form.is_valid():
            qs = self.filter_form.filter_qs(qs)

        return qs

    @cached_property
    def filter_form(self):
        return TicketRequestSearchFilterForm(request=self.request, data=self.request.GET)


@event_permission_required("can_change_event_settings")
def approve(request, organizer, event, ticket_request):
    ticket_request = request.event.ticket_requests.get(id=ticket_request)
    ticket_request.approve(user=request.user)

    messages.success(request, _('Ticket has been approved.'))
    return redirect('plugins:pretix_ticket_request:list',
                    organizer=request.event.organizer.slug,
                    event=request.event.slug)


@event_permission_required("can_change_event_settings")
def reject(request, organizer, event, ticket_request):
    ticket_request = request.event.ticket_requests.get(id=ticket_request)
    ticket_request.reject(user=request.user)

    messages.success(request, _('Ticket has been rejected.'))
    return redirect('plugins:pretix_ticket_request:list',
                    organizer=request.event.organizer.slug,
                    event=request.event.slug)


class TicketRequestDetailMixin:
    def get_object(self, queryset=None):
        url = resolve(self.request.path_info)
        try:
            return self.request.event.ticket_requests.get(id=url.kwargs['ticket_request'])
        except TicketRequest.DoesNotExist:
            raise Http404(_("The requested ticket request does not exist."))

    def get_success_url(self):
        return reverse(
            'plugins:pretix_ticket_request:list',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )


class TicketRequestUpdate(EventPermissionRequiredMixin, TicketRequestDetailMixin, UpdateView):
    form_class = forms.TicketRequestForm
    model = TicketRequest
    template_name = 'pretix_ticket_request/detail.html'
    permission = 'can_change_event_settings'
    context_object_name = 'ticket_request'

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


class TicketRequestCreate(FormView):
    form_class = forms.TicketRequestForm
    template_name = 'pretix_ticket_request/request.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

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


class AttendeeList(EventPermissionRequiredMixin, PaginationMixin, ListView):
    model = Attendee
    context_object_name = 'attendees'
    paginate_by = 20
    template_name = 'pretix_ticket_request/attendees/index.html'
    permission = 'can_change_event_settings'

    def get_queryset(self):
        qs = Attendee.objects.filter(
            event=self.request.event
        )
        return qs


class AttendeeDetailMixin:
    def get_object(self, queryset=None):
        url = resolve(self.request.path_info)
        try:
            return self.request.event.attendees.get(id=url.kwargs['attendee'])
        except Attendee.DoesNotExist:
            raise Http404(_("The requested attendee does not exist."))

    def get_success_url(self):
        return reverse(
            'plugins:pretix_ticket_request:attendee_list',
            kwargs={
                'organizer': self.request.event.organizer.slug,
                'event': self.request.event.slug,
            },
        )


class AttendeeDetail(EventPermissionRequiredMixin, AttendeeDetailMixin, UpdateView):
    form_class = forms.AttendeeDetailForm
    model = Attendee
    template_name = 'pretix_ticket_request/attendees/detail.html'
    permission = 'can_change_event_settings'
    context_object_name = 'attendee'

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _('Your changes have been saved.'))
        if form.has_changed():
            self.object.log_action(
                'pretix.attendee_profile.changed', user=self.request.user, data={
                    k: form.cleaned_data.get(k) for k in form.changed_data
                }
            )
        return super().form_valid(form)


class VerifyAccountStep(CartMixin, TemplateFlowStep):
    priority = 51
    identifier = "verify"
    template_name = 'pretix_ticket_request/checkout_steps/verify.html'
    label = 'Verify email'
    icon = 'check'

    def is_applicable(self, request):
        return True

    def is_completed(self, request, warn=False):
        self.request = request

        return self.cart_session['verification_code_matches']

    def get(self, request):
        self.request = request
        event = self.request.event
        email = self.cart_session['email']
        resend_code = request.GET.get('resend_code')

        # send code and redirect to remove querystring
        if resend_code:
            self.send_verification_email(event, email)
            self.cart_session['verification_code_matches'] = False
            self.cart_session['verification_email_sent'] = True

            return redirect(request.build_absolute_uri(request.path))

        if self.cart_session.get('verification_email_sent'):
            return self.render()

        self.send_verification_email(event, email)
        self.cart_session['verification_code_matches'] = False
        self.cart_session['verification_email_sent'] = True

        return self.render()

    def post(self, request):
        self.request = request
        event = self.request.event

        if not self.form.is_valid():
            return self.render()

        data = self.form.cleaned_data
        email = self.cart_session.get('email')

        # check if code matches
        verification_code_matches = self.cart_session.get('verification_code') == data.get('verification_code')

        # render error if code doesn't match
        if not verification_code_matches:
            messages.warning(request, _("Verification code doesn't match."))
            return self.render()

        # create Attendee
        attendee, created = self.request.event.attendees.get_or_create(email=email)

        if created:
            attendee.verified = True

        attendee.save()

        self.cart_session['verification_code_matches'] = True
        self.cart_session['attendee_id'] = attendee.id

        return redirect(self.get_next_url(request))

    def send_verification_email(self, event, email):
        mailer = VerificationCodeMailer(event=self.event, email=email)
        mailer.send()

        # persist email and code in session
        self.cart_session['email'] = email
        self.cart_session['verification_code'] = mailer.code

    @cached_property
    def form(self):
        f = forms.VerifyAccountStepForm(data=self.request.POST if self.request.method == "POST" else None,
                                        event=self.request.event,
                                        request=self.request)

        return f

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['cart'] = self.get_cart()
        return ctx


class AttendeeProfileStep(CartMixin, TemplateFlowStep):
    priority = 52
    identifier = "profile"
    template_name = 'pretix_ticket_request/checkout_steps/profile.html'
    label = 'Your profile'
    icon = 'user'

    def is_applicable(self, request):
        return True

    def is_completed(self, request, warn=False):
        self.request = request
        attendee_id = self.cart_session['attendee_id']

        if attendee_id:
            attendee = self.request.event.attendees.get(id=attendee_id)
            return attendee.has_profile()

        return True

    def post(self, request):
        self.request = request
        event = self.request.event

        if not self.form.is_valid():
            return self.render()

        attendee = self.form.save()

        # go to next step
        return redirect(self.get_next_url(request))

    @cached_property
    def form(self):
        attendee_id = self.cart_session['attendee_id']
        self.attendee = self.request.event.attendees.get(id=attendee_id)

        initial = self.attendee.profile
        initial['email'] = self.attendee.email

        f = forms.AttendeeProfileForm(data=self.request.POST if self.request.method == "POST" else None,
                                      attendee=self.attendee, initial=initial)

        return f

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['cart'] = self.get_cart()
        return ctx
