"""
Pytest fixtures for Schedules module tests.
"""
import os
import pytest
from datetime import date, time, timedelta

from django.test import Client
from django.utils import timezone


os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


@pytest.fixture
def hub_id(hub_config):
    """Hub ID from HubConfig singleton."""
    return hub_config.hub_id


@pytest.fixture
def schedule_settings(hub_id):
    """Create ScheduleSettings for the test hub."""
    from schedules.models import ScheduleSettings

    return ScheduleSettings.get_settings(hub_id)


@pytest.fixture
def business_hours_week(hub_id):
    """Create a full week of business hours (Mon-Fri open, Sat-Sun closed)."""
    from schedules.models import BusinessHours

    hours = []
    for day in range(5):  # Monday to Friday
        h = BusinessHours.objects.create(
            hub_id=hub_id,
            day_of_week=day,
            open_time=time(9, 0),
            close_time=time(18, 0),
            is_closed=False,
        )
        hours.append(h)

    # Saturday: half day
    h = BusinessHours.objects.create(
        hub_id=hub_id,
        day_of_week=5,
        open_time=time(10, 0),
        close_time=time(14, 0),
        is_closed=False,
    )
    hours.append(h)

    # Sunday: closed
    h = BusinessHours.objects.create(
        hub_id=hub_id,
        day_of_week=6,
        open_time=time(9, 0),
        close_time=time(18, 0),
        is_closed=True,
    )
    hours.append(h)

    return hours


@pytest.fixture
def monday_hours(hub_id):
    """Create business hours for Monday with a break."""
    from schedules.models import BusinessHours

    return BusinessHours.objects.create(
        hub_id=hub_id,
        day_of_week=0,
        open_time=time(9, 0),
        close_time=time(18, 0),
        is_closed=False,
        break_start=time(13, 0),
        break_end=time(14, 0),
    )


@pytest.fixture
def special_day(hub_id):
    """Create a special day (Christmas)."""
    from schedules.models import SpecialDay

    return SpecialDay.objects.create(
        hub_id=hub_id,
        date=date(2026, 12, 25),
        name='Christmas',
        is_closed=True,
        recurring_yearly=True,
        notes='Merry Christmas!',
    )


@pytest.fixture
def special_day_reduced(hub_id):
    """Create a special day with reduced hours."""
    from schedules.models import SpecialDay

    return SpecialDay.objects.create(
        hub_id=hub_id,
        date=date(2026, 12, 24),
        name='Christmas Eve',
        is_closed=False,
        open_time=time(9, 0),
        close_time=time(14, 0),
        recurring_yearly=True,
    )


@pytest.fixture
def schedule_override(hub_id):
    """Create a schedule override (summer hours)."""
    from schedules.models import ScheduleOverride

    return ScheduleOverride.objects.create(
        hub_id=hub_id,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 31),
        reason='Summer hours',
        open_time=time(8, 0),
        close_time=time(15, 0),
        is_closed=False,
    )


@pytest.fixture
def employee(db):
    """Create a local user (employee)."""
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='Test Employee',
        email='employee@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    """Authenticated Django test client."""
    client = Client()
    session = client.session
    session['local_user_id'] = str(employee.id)
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session['user_role'] = employee.role
    session['store_config_checked'] = True
    session.save()
    return client
