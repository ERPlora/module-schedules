from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ---------------------------------------------------------------------------
# Day-of-week choices (ISO: 0=Monday .. 6=Sunday)
# ---------------------------------------------------------------------------

DAY_OF_WEEK_CHOICES = [
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
]


# ---------------------------------------------------------------------------
# Schedule Settings
# ---------------------------------------------------------------------------

class ScheduleSettings(HubBaseModel):
    """Per-hub schedule configuration."""

    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='Europe/Madrid',
        help_text=_('IANA timezone for this hub (e.g. Europe/Madrid, America/New_York).'),
    )
    week_starts_on = models.IntegerField(
        _('Week Starts On'),
        default=1,
        help_text=_('1=Monday, 7=Sunday'),
    )
    slot_duration = models.IntegerField(
        _('Slot Duration'),
        default=30,
        help_text=_('Default time slot in minutes'),
    )
    auto_close_enabled = models.BooleanField(
        _('Auto Close Enabled'),
        default=False,
        help_text=_('Automatically mark the business as closed after closing time.'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'schedules_settings'
        verbose_name = _('Schedule Settings')
        verbose_name_plural = _('Schedule Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f"Schedule Settings (hub {self.hub_id})"

    @classmethod
    def get_settings(cls, hub_id):
        """Get or create the singleton settings for a hub."""
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# ---------------------------------------------------------------------------
# Business Hours
# ---------------------------------------------------------------------------

class BusinessHours(HubBaseModel):
    """Regular weekly business hours (one row per day of week per hub)."""

    day_of_week = models.IntegerField(
        _('Day of Week'),
        choices=DAY_OF_WEEK_CHOICES,
        help_text=_('0=Monday, 6=Sunday'),
    )
    open_time = models.TimeField(
        _('Open Time'),
        default=time(9, 0),
    )
    close_time = models.TimeField(
        _('Close Time'),
        default=time(18, 0),
    )
    is_closed = models.BooleanField(
        _('Closed'),
        default=False,
        help_text=_('If checked, the business is closed on this day.'),
    )
    break_start = models.TimeField(
        _('Break Start'),
        null=True,
        blank=True,
        help_text=_('Start of midday break (optional).'),
    )
    break_end = models.TimeField(
        _('Break End'),
        null=True,
        blank=True,
        help_text=_('End of midday break (optional).'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'schedules_business_hours'
        verbose_name = _('Business Hours')
        verbose_name_plural = _('Business Hours')
        unique_together = [('hub_id', 'day_of_week')]
        ordering = ['day_of_week']

    def __str__(self):
        day_label = dict(DAY_OF_WEEK_CHOICES).get(self.day_of_week, self.day_of_week)
        if self.is_closed:
            return f"{day_label}: Closed"
        return f"{day_label}: {self.open_time:%H:%M}-{self.close_time:%H:%M}"

    def clean(self):
        """Validate that open < close and break falls within open hours."""
        super().clean()

        if not self.is_closed:
            if self.open_time and self.close_time and self.open_time >= self.close_time:
                raise ValidationError(
                    _('Open time must be before close time.')
                )

            if self.break_start and self.break_end:
                if self.break_start >= self.break_end:
                    raise ValidationError(
                        _('Break start must be before break end.')
                    )
                if self.open_time and self.break_start < self.open_time:
                    raise ValidationError(
                        _('Break start must be after open time.')
                    )
                if self.close_time and self.break_end > self.close_time:
                    raise ValidationError(
                        _('Break end must be before close time.')
                    )

    def is_open_at(self, check_time):
        """Check if the business is open at a given time on this day."""
        if self.is_closed:
            return False

        if not (self.open_time <= check_time < self.close_time):
            return False

        # Check break period
        if self.break_start and self.break_end:
            if self.break_start <= check_time < self.break_end:
                return False

        return True

    def get_slots(self):
        """Return list of available time slots based on settings."""
        if self.is_closed:
            return []

        try:
            settings = ScheduleSettings.get_settings(self.hub_id)
            duration = settings.slot_duration
        except Exception:
            duration = 30

        slots = []
        current = self.open_time

        while current < self.close_time:
            # Skip break period
            if self.break_start and self.break_end:
                if self.break_start <= current < self.break_end:
                    current = self.break_end
                    continue

            slots.append(current)

            # Advance by slot_duration minutes
            dt = timedelta(minutes=duration)
            hour = current.hour
            minute = current.minute
            total_minutes = hour * 60 + minute + duration
            new_hour = total_minutes // 60
            new_minute = total_minutes % 60

            if new_hour >= 24:
                break

            current = time(new_hour, new_minute)

        return slots


# ---------------------------------------------------------------------------
# Special Day
# ---------------------------------------------------------------------------

class SpecialDay(HubBaseModel):
    """Holidays, special hours, or other non-regular schedule days."""

    date = models.DateField(
        _('Date'),
    )
    name = models.CharField(
        _('Name'),
        max_length=200,
        help_text=_('Name of the holiday or special day.'),
    )
    is_closed = models.BooleanField(
        _('Closed'),
        default=True,
        help_text=_('If checked, the business is fully closed on this day.'),
    )
    open_time = models.TimeField(
        _('Open Time'),
        null=True,
        blank=True,
        help_text=_('Special open time (only if not fully closed).'),
    )
    close_time = models.TimeField(
        _('Close Time'),
        null=True,
        blank=True,
        help_text=_('Special close time (only if not fully closed).'),
    )
    recurring_yearly = models.BooleanField(
        _('Recurring Yearly'),
        default=False,
        help_text=_('If checked, this special day recurs every year on the same date.'),
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        default='',
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'schedules_special_day'
        verbose_name = _('Special Day')
        verbose_name_plural = _('Special Days')
        unique_together = [('hub_id', 'date')]
        ordering = ['date']

    def __str__(self):
        status = _('Closed') if self.is_closed else f"{self.open_time:%H:%M}-{self.close_time:%H:%M}"
        return f"{self.name} ({self.date}): {status}"

    def clean(self):
        """Validate that times are provided when not fully closed."""
        super().clean()

        if not self.is_closed:
            if not self.open_time or not self.close_time:
                raise ValidationError(
                    _('Open time and close time are required when the day is not fully closed.')
                )
            if self.open_time >= self.close_time:
                raise ValidationError(
                    _('Open time must be before close time.')
                )


# ---------------------------------------------------------------------------
# Schedule Override
# ---------------------------------------------------------------------------

class ScheduleOverride(HubBaseModel):
    """Temporary schedule change for a date range (e.g. extended holiday hours)."""

    start_date = models.DateField(
        _('Start Date'),
    )
    end_date = models.DateField(
        _('End Date'),
    )
    reason = models.CharField(
        _('Reason'),
        max_length=200,
        help_text=_('Reason for the schedule override.'),
    )
    open_time = models.TimeField(
        _('Open Time'),
        null=True,
        blank=True,
        help_text=_('Override open time (leave empty to use regular hours).'),
    )
    close_time = models.TimeField(
        _('Close Time'),
        null=True,
        blank=True,
        help_text=_('Override close time (leave empty to use regular hours).'),
    )
    is_closed = models.BooleanField(
        _('Closed'),
        default=False,
        help_text=_('If checked, the business is fully closed during this period.'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'schedules_override'
        verbose_name = _('Schedule Override')
        verbose_name_plural = _('Schedule Overrides')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.reason} ({self.start_date} - {self.end_date})"

    def clean(self):
        """Validate that start_date <= end_date."""
        super().clean()

        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(
                    _('Start date must be on or before end date.')
                )
