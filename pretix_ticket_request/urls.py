from django.conf.urls import url

from .views import SettingsView

urlpatterns = [
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-requests/settings/',
        SettingsView.as_view(),
        name='settings',
    ),
    url(
        r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/ticket-requests/',
        SettingsView.as_view(),
        name='control',
    ),
]
