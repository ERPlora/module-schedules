from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SchedulesAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schedules'
    label = 'schedules'
    verbose_name = _('Schedules')

    def ready(self):
        pass
