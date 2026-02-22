from django import forms
from django.utils.translation import gettext_lazy as _

from .models import BusinessHours, SpecialDay, ScheduleSettings


class BusinessHoursForm(forms.ModelForm):
    """Form for editing business hours for a single day."""

    class Meta:
        model = BusinessHours
        fields = [
            'day_of_week', 'open_time', 'close_time',
            'is_closed', 'break_start', 'break_end',
        ]
        widgets = {
            'day_of_week': forms.Select(attrs={
                'class': 'select',
            }),
            'open_time': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
            'close_time': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
            'is_closed': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'break_start': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
            'break_end': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
        }


class SpecialDayForm(forms.ModelForm):
    """Form for creating and editing special days (holidays)."""

    class Meta:
        model = SpecialDay
        fields = [
            'date', 'name', 'is_closed',
            'open_time', 'close_time',
            'recurring_yearly', 'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'input',
                'type': 'date',
            }),
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Holiday name'),
            }),
            'is_closed': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'open_time': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
            'close_time': forms.TimeInput(attrs={
                'class': 'input',
                'type': 'time',
            }),
            'recurring_yearly': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '3',
                'placeholder': _('Additional notes...'),
            }),
        }


class ScheduleSettingsForm(forms.ModelForm):
    """Form for schedule module settings."""

    class Meta:
        model = ScheduleSettings
        fields = [
            'timezone', 'week_starts_on', 'slot_duration',
            'auto_close_enabled',
        ]
        widgets = {
            'timezone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('e.g. Europe/Madrid'),
            }),
            'week_starts_on': forms.Select(
                choices=[
                    (1, _('Monday')),
                    (2, _('Tuesday')),
                    (3, _('Wednesday')),
                    (4, _('Thursday')),
                    (5, _('Friday')),
                    (6, _('Saturday')),
                    (7, _('Sunday')),
                ],
                attrs={
                    'class': 'select',
                },
            ),
            'slot_duration': forms.NumberInput(attrs={
                'class': 'input',
                'min': '5',
                'max': '120',
                'step': '5',
            }),
            'auto_close_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }
