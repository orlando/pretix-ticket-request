from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-requests/settings/',
        views.TicketRequestSettings.as_view(),
        name='settings',
    ),
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-requests/',
        views.TicketRequestList.as_view(),
        name='list',
    ),
]

event_patterns = [
    url(r'^ticket-request/', views.TicketRequestCreate.as_view(), name='request'),
]
