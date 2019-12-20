from django.utils.translation import ugettext_lazy
try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    name = 'pretix_ticket_request'
    verbose_name = 'Pretix Ticket Request'

    class PretixPluginMeta:
        name = ugettext_lazy('Pretix Ticket Request')
        author = 'Orlando Del Aguila'
        description = ugettext_lazy('Ticket request functionality for Pretix')
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_ticket_request.PluginApp'
