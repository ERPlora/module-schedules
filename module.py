from django.utils.translation import gettext_lazy as _

MODULE_ID = 'schedules'
MODULE_NAME = _('Schedules')
MODULE_VERSION = '1.0.0'
MODULE_ICON = 'calendar-outline'
MODULE_DESCRIPTION = _('Business hours, holiday schedules, and availability management')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = 'utilities'

MENU = {
    'label': _('Schedules'),
    'icon': 'calendar-outline',
    'order': 80,
}

NAVIGATION = [
    {'label': _('Hours'), 'icon': 'time-outline', 'id': 'dashboard'},
    {'label': _('Special Days'), 'icon': 'calendar-outline', 'id': 'special_days'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

DEPENDENCIES = []

PERMISSIONS = [
    'schedules.view_schedule',
    'schedules.add_schedule',
    'schedules.change_schedule',
    'schedules.delete_schedule',
    'schedules.manage_settings',
]
