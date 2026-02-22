"""
Integration tests for Schedules views.
"""

import json
import uuid
import pytest
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import Client
from django.urls import reverse


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_hub_config(db, settings):
    """Ensure HubConfig + StoreConfig exist."""
    from apps.configuration.models import HubConfig, StoreConfig
    config = HubConfig.get_solo()
    config.save()
    store = StoreConfig.get_solo()
    store.business_name = 'Test Business'
    store.is_configured = True
    store.save()


@pytest.fixture
def hub_id(db):
    from apps.configuration.models import HubConfig
    return HubConfig.get_solo().hub_id


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


@pytest.fixture
def schedule_settings(hub_id):
    from schedules.models import ScheduleSettings
    return ScheduleSettings.get_settings(hub_id)


@pytest.fixture
def monday_hours(hub_id):
    from schedules.models import BusinessHours
    return BusinessHours.objects.create(
        hub_id=hub_id,
        day_of_week=0,
        open_time=time(9, 0),
        close_time=time(18, 0),
        is_closed=False,
    )


@pytest.fixture
def special_day(hub_id):
    from schedules.models import SpecialDay
    return SpecialDay.objects.create(
        hub_id=hub_id,
        date=date(2026, 12, 25),
        name='Christmas',
        is_closed=True,
        recurring_yearly=True,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/schedules/')
        assert response.status_code == 302

    def test_dashboard_loads(self, auth_client):
        response = auth_client.get('/m/schedules/')
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get('/m/schedules/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_dashboard_with_hours(self, auth_client, monday_hours):
        response = auth_client.get('/m/schedules/')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Edit Hours
# ---------------------------------------------------------------------------

class TestEditHours:

    def test_edit_hours_create(self, auth_client, hub_id):
        from schedules.models import BusinessHours
        response = auth_client.post(
            '/m/schedules/hours/edit/',
            data=json.dumps({
                'day_of_week': 0,
                'is_closed': False,
                'open_time': '09:00',
                'close_time': '18:00',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert BusinessHours.objects.filter(hub_id=hub_id, day_of_week=0).exists()

    def test_edit_hours_update(self, auth_client, monday_hours):
        response = auth_client.post(
            '/m/schedules/hours/edit/',
            data=json.dumps({
                'day_of_week': 0,
                'is_closed': False,
                'open_time': '10:00',
                'close_time': '20:00',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        monday_hours.refresh_from_db()
        assert monday_hours.open_time == time(10, 0)
        assert monday_hours.close_time == time(20, 0)

    def test_edit_hours_close_day(self, auth_client, monday_hours):
        response = auth_client.post(
            '/m/schedules/hours/edit/',
            data=json.dumps({
                'day_of_week': 0,
                'is_closed': True,
                'open_time': '09:00',
                'close_time': '18:00',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        monday_hours.refresh_from_db()
        assert monday_hours.is_closed is True

    def test_edit_hours_with_break(self, auth_client, hub_id):
        from schedules.models import BusinessHours
        response = auth_client.post(
            '/m/schedules/hours/edit/',
            data=json.dumps({
                'day_of_week': 1,
                'is_closed': False,
                'open_time': '09:00',
                'close_time': '18:00',
                'break_start': '13:00',
                'break_end': '14:00',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        h = BusinessHours.objects.get(hub_id=hub_id, day_of_week=1)
        assert h.break_start == time(13, 0)
        assert h.break_end == time(14, 0)

    def test_edit_hours_requires_login(self):
        client = Client()
        response = client.post(
            '/m/schedules/hours/edit/',
            data=json.dumps({'day_of_week': 0, 'is_closed': True}),
            content_type='application/json',
        )
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Special Days
# ---------------------------------------------------------------------------

class TestSpecialDays:

    def test_special_days_loads(self, auth_client):
        response = auth_client.get('/m/schedules/special-days/')
        assert response.status_code == 200

    def test_special_days_with_data(self, auth_client, special_day):
        response = auth_client.get('/m/schedules/special-days/')
        assert response.status_code == 200

    def test_add_special_day(self, auth_client, hub_id):
        from schedules.models import SpecialDay
        response = auth_client.post(
            '/m/schedules/special-days/add/',
            data=json.dumps({
                'date': '2026-01-06',
                'name': 'Three Kings Day',
                'is_closed': True,
                'recurring_yearly': True,
                'notes': 'Epiphany',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        assert SpecialDay.objects.filter(hub_id=hub_id, name='Three Kings Day').exists()

    def test_add_special_day_with_hours(self, auth_client, hub_id):
        response = auth_client.post(
            '/m/schedules/special-days/add/',
            data=json.dumps({
                'date': '2026-12-24',
                'name': 'Christmas Eve',
                'is_closed': False,
                'open_time': '09:00',
                'close_time': '14:00',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True

    def test_edit_special_day(self, auth_client, special_day):
        response = auth_client.post(
            f'/m/schedules/special-days/{special_day.pk}/edit/',
            data=json.dumps({
                'date': '2026-12-25',
                'name': 'Navidad',
                'is_closed': True,
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        special_day.refresh_from_db()
        assert special_day.name == 'Navidad'

    def test_delete_special_day(self, auth_client, special_day):
        from schedules.models import SpecialDay
        response = auth_client.post(
            f'/m/schedules/special-days/{special_day.pk}/delete/',
        )
        data = response.json()
        assert data['success'] is True
        assert SpecialDay.objects.filter(pk=special_day.pk).count() == 0

    def test_delete_nonexistent(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.post(f'/m/schedules/special-days/{fake_uuid}/delete/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Is Open Now API
# ---------------------------------------------------------------------------

class TestIsOpenNow:

    def test_api_returns_json(self, auth_client):
        response = auth_client.get('/m/schedules/api/is-open/')
        assert response.status_code == 200
        data = response.json()
        assert 'is_open' in data
        assert 'reason' in data
        assert 'today' in data
        assert 'current_time' in data

    def test_api_with_no_hours(self, auth_client):
        response = auth_client.get('/m/schedules/api/is-open/')
        data = response.json()
        assert data['is_open'] is False

    def test_api_requires_login(self):
        client = Client()
        response = client.get('/m/schedules/api/is-open/')
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettingsView:

    def test_settings_loads(self, auth_client):
        response = auth_client.get('/m/schedules/settings/')
        assert response.status_code == 200

    def test_settings_save(self, auth_client, hub_id, schedule_settings):
        from schedules.models import ScheduleSettings
        response = auth_client.post(
            '/m/schedules/settings/save/',
            data=json.dumps({
                'timezone': 'America/New_York',
                'week_starts_on': 7,
                'slot_duration': 15,
                'auto_close_enabled': True,
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        refreshed = ScheduleSettings.get_settings(hub_id)
        assert refreshed.timezone == 'America/New_York'
        assert refreshed.week_starts_on == 7
        assert refreshed.slot_duration == 15
        assert refreshed.auto_close_enabled is True

    def test_settings_save_partial(self, auth_client, hub_id, schedule_settings):
        """Saving only some fields should keep others unchanged."""
        from schedules.models import ScheduleSettings
        response = auth_client.post(
            '/m/schedules/settings/save/',
            data=json.dumps({
                'timezone': 'Asia/Tokyo',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True

        refreshed = ScheduleSettings.get_settings(hub_id)
        assert refreshed.timezone == 'Asia/Tokyo'
        assert refreshed.slot_duration == 30  # unchanged

    def test_settings_requires_login(self):
        client = Client()
        response = client.post(
            '/m/schedules/settings/save/',
            data=json.dumps({'timezone': 'UTC'}),
            content_type='application/json',
        )
        assert response.status_code == 302
