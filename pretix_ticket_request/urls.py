from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-request/settings/$',
        views.TicketRequestSettings.as_view(),
        name='settings',
    ),
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-request/$',
        views.TicketRequestList.as_view(),
        name='list',
    ),
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-request/(?P<ticket_request>\d+)/$',
        views.TicketRequestUpdate.as_view(),
        name='update',
    ),
]

event_patterns = [
    url(r'^ticket-request/$', views.TicketRequestCreate.as_view(), name='request'),
]
