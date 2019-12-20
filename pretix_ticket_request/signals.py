from django.db.models import QuerySet
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from i18nfield.strings import LazyI18nString
from pretix.control.signals import nav_event


@receiver(nav_event, dispatch_uid='pretix_ticket_request_nav')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            'label': _('Ticket Requests'),
            'icon': 'flag',
            'url': reverse(
                'plugins:pretix_ticket_request:control',
                kwargs={
                    'event': request.event.slug,
                    'organizer': request.organizer.slug,
                },
            ),
            'active': url.namespace == 'plugins:pretix_ticket_request',
        }
    ]
