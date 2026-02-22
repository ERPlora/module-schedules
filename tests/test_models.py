"""
Unit tests for Schedules models.
"""

import pytest
from datetime import date, time, timedelta
from django.core.exceptions import ValidationError


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# ScheduleSettings
# ---------------------------------------------------------------------------

class TestScheduleSettings:
    """Tests for ScheduleSettings model."""

    def test_settings_created_with_defaults(self, hub_config):
        from schedules.models import ScheduleSettings
        settings = ScheduleSettings.objects.create(hub_id=hub_config.hub_id)
        assert settings.timezone == 'Europe/Madrid'
        assert settings.week_starts_on == 1
        assert settings.slot_duration == 30
        assert settings.auto_close_enabled is False

    def test_get_settings_creates_singleton(self, hub_id):
        from schedules.models import ScheduleSettings
        s = ScheduleSettings.get_settings(hub_id)
        assert s is not None
        assert s.hub_id == hub_id

    def test_get_settings_returns_existing(self, hub_id):
        from schedules.models import ScheduleSettings
        s1 = ScheduleSettings.get_settings(hub_id)
        s2 = ScheduleSettings.get_settings(hub_id)
        assert s1.pk == s2.pk

    def test_str(self, schedule_settings):
        assert 'Schedule Settings' in str(schedule_settings)

    def test_update_settings(self, schedule_settings):
        from schedules.models import ScheduleSettings
        schedule_settings.timezone = 'America/New_York'
        schedule_settings.week_starts_on = 7
        schedule_settings.slot_duration = 15
        schedule_settings.auto_close_enabled = True
        schedule_settings.save()

        refreshed = ScheduleSettings.get_settings(schedule_settings.hub_id)
        assert refreshed.timezone == 'America/New_York'
        assert refreshed.week_starts_on == 7
        assert refreshed.slot_duration == 15
        assert refreshed.auto_close_enabled is True

    def test_unique_per_hub(self, hub_id):
        """unique_together on hub_id prevents duplicate settings."""
        from schedules.models import ScheduleSettings
        unique = ScheduleSettings._meta.unique_together
        assert ('hub_id',) in unique


# ---------------------------------------------------------------------------
# BusinessHours
# ---------------------------------------------------------------------------

class TestBusinessHours:
    """Tests for BusinessHours model."""

    def test_create(self, monday_hours):
        assert monday_hours.day_of_week == 0
        assert monday_hours.open_time == time(9, 0)
        assert monday_hours.close_time == time(18, 0)
        assert monday_hours.is_closed is False
        assert monday_hours.break_start == time(13, 0)
        assert monday_hours.break_end == time(14, 0)

    def test_str_open(self, monday_hours):
        result = str(monday_hours)
        assert 'Monday' in result
        assert '09:00' in result
        assert '18:00' in result

    def test_str_closed(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours.objects.create(
            hub_id=hub_id, day_of_week=6,
            is_closed=True,
        )
        result = str(h)
        assert 'Sunday' in result
        assert 'Closed' in result

    def test_full_week(self, business_hours_week):
        assert len(business_hours_week) == 7

    def test_ordering(self, business_hours_week):
        from schedules.models import BusinessHours
        hours = list(BusinessHours.objects.filter(
            hub_id=business_hours_week[0].hub_id,
        ))
        days = [h.day_of_week for h in hours]
        assert days == sorted(days)

    def test_unique_together(self, hub_id):
        """unique_together on (hub_id, day_of_week)."""
        from schedules.models import BusinessHours
        unique = BusinessHours._meta.unique_together
        assert ('hub_id', 'day_of_week') in unique

    def test_validation_open_before_close(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(18, 0),
            close_time=time(9, 0),
            is_closed=False,
        )
        with pytest.raises(ValidationError):
            h.clean()

    def test_validation_open_equals_close(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(9, 0),
            is_closed=False,
        )
        with pytest.raises(ValidationError):
            h.clean()

    def test_validation_break_start_before_end(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(18, 0),
            is_closed=False,
            break_start=time(14, 0),
            break_end=time(13, 0),
        )
        with pytest.raises(ValidationError):
            h.clean()

    def test_validation_break_before_open(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(18, 0),
            is_closed=False,
            break_start=time(8, 0),
            break_end=time(9, 30),
        )
        with pytest.raises(ValidationError):
            h.clean()

    def test_validation_break_after_close(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(18, 0),
            is_closed=False,
            break_start=time(17, 0),
            break_end=time(19, 0),
        )
        with pytest.raises(ValidationError):
            h.clean()

    def test_validation_skipped_when_closed(self, hub_id):
        """Validation should pass when day is closed, even with bad times."""
        from schedules.models import BusinessHours
        h = BusinessHours(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(18, 0),
            close_time=time(9, 0),
            is_closed=True,
        )
        h.clean()  # Should not raise

    def test_is_open_at_during_hours(self, monday_hours):
        assert monday_hours.is_open_at(time(10, 0)) is True
        assert monday_hours.is_open_at(time(15, 0)) is True

    def test_is_open_at_before_open(self, monday_hours):
        assert monday_hours.is_open_at(time(8, 0)) is False

    def test_is_open_at_after_close(self, monday_hours):
        assert monday_hours.is_open_at(time(18, 0)) is False
        assert monday_hours.is_open_at(time(19, 0)) is False

    def test_is_open_at_during_break(self, monday_hours):
        assert monday_hours.is_open_at(time(13, 0)) is False
        assert monday_hours.is_open_at(time(13, 30)) is False

    def test_is_open_at_after_break(self, monday_hours):
        assert monday_hours.is_open_at(time(14, 0)) is True

    def test_is_open_at_closed_day(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours.objects.create(
            hub_id=hub_id, day_of_week=6, is_closed=True,
        )
        assert h.is_open_at(time(12, 0)) is False

    def test_get_slots_normal(self, hub_id, schedule_settings):
        """Test slot generation with 30-minute default."""
        from schedules.models import BusinessHours
        h = BusinessHours.objects.create(
            hub_id=hub_id,
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(12, 0),
            is_closed=False,
        )
        slots = h.get_slots()
        # 9:00, 9:30, 10:00, 10:30, 11:00, 11:30
        assert len(slots) == 6
        assert slots[0] == time(9, 0)
        assert slots[-1] == time(11, 30)

    def test_get_slots_with_break(self, monday_hours, schedule_settings):
        """Test slots skip the break period."""
        slots = monday_hours.get_slots()
        # Should not include 13:00 or 13:30
        assert time(13, 0) not in slots
        assert time(13, 30) not in slots
        # But 14:00 should be there
        assert time(14, 0) in slots

    def test_get_slots_closed_day(self, hub_id):
        from schedules.models import BusinessHours
        h = BusinessHours.objects.create(
            hub_id=hub_id, day_of_week=6, is_closed=True,
        )
        assert h.get_slots() == []

    def test_soft_delete(self, monday_hours):
        from schedules.models import BusinessHours
        monday_hours.delete()
        assert monday_hours.is_deleted is True
        assert BusinessHours.objects.filter(pk=monday_hours.pk).count() == 0
        assert BusinessHours.all_objects.filter(pk=monday_hours.pk).count() == 1


# ---------------------------------------------------------------------------
# SpecialDay
# ---------------------------------------------------------------------------

class TestSpecialDay:
    """Tests for SpecialDay model."""

    def test_create_closed(self, special_day):
        assert special_day.name == 'Christmas'
        assert special_day.date == date(2026, 12, 25)
        assert special_day.is_closed is True
        assert special_day.recurring_yearly is True
        assert special_day.notes == 'Merry Christmas!'

    def test_create_reduced_hours(self, special_day_reduced):
        assert special_day_reduced.name == 'Christmas Eve'
        assert special_day_reduced.is_closed is False
        assert special_day_reduced.open_time == time(9, 0)
        assert special_day_reduced.close_time == time(14, 0)

    def test_str_closed(self, special_day):
        result = str(special_day)
        assert 'Christmas' in result
        assert '2026-12-25' in result

    def test_str_open(self, special_day_reduced):
        result = str(special_day_reduced)
        assert 'Christmas Eve' in result
        assert '09:00' in result
        assert '14:00' in result

    def test_ordering(self, hub_id):
        from schedules.models import SpecialDay
        SpecialDay.objects.create(
            hub_id=hub_id, date=date(2026, 12, 31), name='New Year Eve', is_closed=True,
        )
        SpecialDay.objects.create(
            hub_id=hub_id, date=date(2026, 1, 1), name='New Year', is_closed=True,
        )
        days = list(SpecialDay.objects.filter(hub_id=hub_id))
        assert days[0].date < days[1].date

    def test_unique_together(self, hub_id):
        from schedules.models import SpecialDay
        unique = SpecialDay._meta.unique_together
        assert ('hub_id', 'date') in unique

    def test_validation_times_required_when_open(self, hub_id):
        from schedules.models import SpecialDay
        sd = SpecialDay(
            hub_id=hub_id,
            date=date(2026, 6, 15),
            name='Half Day',
            is_closed=False,
            open_time=None,
            close_time=None,
        )
        with pytest.raises(ValidationError):
            sd.clean()

    def test_validation_open_before_close(self, hub_id):
        from schedules.models import SpecialDay
        sd = SpecialDay(
            hub_id=hub_id,
            date=date(2026, 6, 15),
            name='Half Day',
            is_closed=False,
            open_time=time(18, 0),
            close_time=time(9, 0),
        )
        with pytest.raises(ValidationError):
            sd.clean()

    def test_validation_passes_when_closed(self, hub_id):
        """Validation should pass when day is closed without times."""
        from schedules.models import SpecialDay
        sd = SpecialDay(
            hub_id=hub_id,
            date=date(2026, 6, 15),
            name='Holiday',
            is_closed=True,
        )
        sd.clean()  # Should not raise

    def test_recurring_yearly(self, special_day):
        assert special_day.recurring_yearly is True

    def test_non_recurring(self, hub_id):
        from schedules.models import SpecialDay
        sd = SpecialDay.objects.create(
            hub_id=hub_id,
            date=date(2026, 3, 15),
            name='One-time event',
            is_closed=True,
            recurring_yearly=False,
        )
        assert sd.recurring_yearly is False

    def test_soft_delete(self, special_day):
        from schedules.models import SpecialDay
        special_day.delete()
        assert special_day.is_deleted is True
        assert SpecialDay.objects.filter(pk=special_day.pk).count() == 0
        assert SpecialDay.all_objects.filter(pk=special_day.pk).count() == 1


# ---------------------------------------------------------------------------
# ScheduleOverride
# ---------------------------------------------------------------------------

class TestScheduleOverride:
    """Tests for ScheduleOverride model."""

    def test_create(self, schedule_override):
        assert schedule_override.reason == 'Summer hours'
        assert schedule_override.start_date == date(2026, 7, 1)
        assert schedule_override.end_date == date(2026, 8, 31)
        assert schedule_override.open_time == time(8, 0)
        assert schedule_override.close_time == time(15, 0)
        assert schedule_override.is_closed is False

    def test_str(self, schedule_override):
        result = str(schedule_override)
        assert 'Summer hours' in result
        assert '2026-07-01' in result
        assert '2026-08-31' in result

    def test_ordering(self, hub_id):
        from schedules.models import ScheduleOverride
        o1 = ScheduleOverride.objects.create(
            hub_id=hub_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
            reason='January special',
        )
        o2 = ScheduleOverride.objects.create(
            hub_id=hub_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
            reason='June special',
        )
        overrides = list(ScheduleOverride.objects.filter(hub_id=hub_id))
        # Ordering is -start_date, so June comes first
        assert overrides[0].pk == o2.pk

    def test_validation_start_before_end(self, hub_id):
        from schedules.models import ScheduleOverride
        o = ScheduleOverride(
            hub_id=hub_id,
            start_date=date(2026, 8, 31),
            end_date=date(2026, 7, 1),
            reason='Invalid',
        )
        with pytest.raises(ValidationError):
            o.clean()

    def test_validation_same_day(self, hub_id):
        """Same start and end date should be valid (single day override)."""
        from schedules.models import ScheduleOverride
        o = ScheduleOverride(
            hub_id=hub_id,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 1),
            reason='Single day',
        )
        o.clean()  # Should not raise

    def test_closed_override(self, hub_id):
        from schedules.models import ScheduleOverride
        o = ScheduleOverride.objects.create(
            hub_id=hub_id,
            start_date=date(2026, 12, 20),
            end_date=date(2026, 12, 31),
            reason='Holiday closure',
            is_closed=True,
        )
        assert o.is_closed is True
        assert o.open_time is None
        assert o.close_time is None

    def test_soft_delete(self, schedule_override):
        from schedules.models import ScheduleOverride
        schedule_override.delete()
        assert schedule_override.is_deleted is True
        assert ScheduleOverride.objects.filter(pk=schedule_override.pk).count() == 0
        assert ScheduleOverride.all_objects.filter(pk=schedule_override.pk).count() == 1
