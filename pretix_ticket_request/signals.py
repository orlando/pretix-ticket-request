from django.db.models import QuerySet
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from i18nfield.strings import LazyI18nString
from django.utils.functional import cached_property
from pretix.control.signals import nav_event
from pretix.presale.signals import (checkout_flow_steps, checkout_all_optional)

from . import views


@receiver(nav_event, dispatch_uid='pretix_ticket_request_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            'label': _('Ticket request'),
            'icon': 'flag',
            'url': reverse(
                'plugins:pretix_ticket_request:list',
                kwargs={
                    'event': request.event.slug,
                    'organizer': request.organizer.slug,
                },
            ),
            'active': False,
            'children': [
                {
                    'label': _('List'),
                    'url': reverse(
                        'plugins:pretix_ticket_request:list',
                        kwargs={
                            'event': request.event.slug,
                            'organizer': request.organizer.slug,
                        },
                    ),
                    'active': url.namespace == 'plugins:pretix_ticket_request' and url.url_name == 'list'
                },
                {
                    'label': _('Settings'),
                    'url': reverse(
                        'plugins:pretix_ticket_request:settings',
                        kwargs={
                            'event': request.event.slug,
                            'organizer': request.organizer.slug,
                        },
                    ),
                    'active': url.namespace == 'plugins:pretix_ticket_request' and url.url_name == 'settings'
                },
            ]
        }
    ]


@receiver(checkout_flow_steps, dispatch_uid='pretix_ticket_request_your_account_step')
def your_account_checkout_step(sender, **kwargs):
    return views.YourAccountStep


@receiver(checkout_flow_steps, dispatch_uid='pretix_ticket_request_verify_account_step')
def verify_account_checkout_step(sender, **kwargs):
    return views.VerifyAccountStep


@receiver(checkout_all_optional, dispatch_uid='pretix_ticket_request_your_information_all_optional')
def your_information_all_optional(sender, **kwargs):
    return True
