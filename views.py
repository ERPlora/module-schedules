import json
from datetime import date, time

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import login_required, permission_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    BusinessHours, ScheduleSettings, SpecialDay, ScheduleOverride,
    DAY_OF_WEEK_CHOICES,
)
from .forms import BusinessHoursForm, SpecialDayForm, ScheduleSettingsForm


def _hub_id(request):
    return request.session.get('hub_id')


# ============================================================================
# Dashboard (Weekly Hours)
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('schedules', 'dashboard')
@htmx_view('schedules/pages/index.html', 'schedules/partials/content.html')
def dashboard(request):
    """Show weekly business hours grid and today's status."""
    hub = _hub_id(request)

    # Get all business hours for this hub, ordered by day
    hours = BusinessHours.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('day_of_week')

    # Build a dict keyed by day_of_week for easy template access
    hours_by_day = {h.day_of_week: h for h in hours}

    # Build full week list (0-6), filling in gaps with None
    week = []
    for day_num, day_label in DAY_OF_WEEK_CHOICES:
        week.append({
            'day_num': day_num,
            'day_label': day_label,
            'hours': hours_by_day.get(day_num),
        })

    # Today's status
    today = timezone.localdate()
    today_weekday = today.weekday()  # 0=Monday in Python
    today_hours = hours_by_day.get(today_weekday)
    now_time = timezone.localtime().time()

    is_open = False
    if today_hours and not today_hours.is_closed:
        is_open = today_hours.is_open_at(now_time)

    # Check for special day override
    special_today = SpecialDay.objects.filter(
        hub_id=hub, is_deleted=False, date=today,
    ).first()
    if special_today:
        if special_today.is_closed:
            is_open = False
        elif special_today.open_time and special_today.close_time:
            is_open = special_today.open_time <= now_time < special_today.close_time

    # Check for schedule override
    override_today = ScheduleOverride.objects.filter(
        hub_id=hub, is_deleted=False,
        start_date__lte=today, end_date__gte=today,
    ).first()
    if override_today:
        if override_today.is_closed:
            is_open = False
        elif override_today.open_time and override_today.close_time:
            is_open = override_today.open_time <= now_time < override_today.close_time

    # Next special day
    next_special = SpecialDay.objects.filter(
        hub_id=hub, is_deleted=False, date__gte=today,
    ).order_by('date').first()

    return {
        'week': week,
        'today_hours': today_hours,
        'is_open': is_open,
        'special_today': special_today,
        'override_today': override_today,
        'next_special': next_special,
        'day_choices': DAY_OF_WEEK_CHOICES,
    }


# ============================================================================
# Edit Hours
# ============================================================================

@require_http_methods(["POST"])
@login_required
def edit_hours(request):
    """Save or update BusinessHours for a specific day."""
    hub = _hub_id(request)

    try:
        data = json.loads(request.body)
        day_of_week = int(data.get('day_of_week', 0))
        is_closed = data.get('is_closed', False)
        open_time = data.get('open_time', '09:00')
        close_time = data.get('close_time', '18:00')
        break_start = data.get('break_start') or None
        break_end = data.get('break_end') or None

        hours, created = BusinessHours.all_objects.get_or_create(
            hub_id=hub,
            day_of_week=day_of_week,
            defaults={
                'is_closed': is_closed,
                'open_time': open_time,
                'close_time': close_time,
                'break_start': break_start,
                'break_end': break_end,
            },
        )

        if not created:
            hours.is_closed = is_closed
            hours.open_time = open_time
            hours.close_time = close_time
            hours.break_start = break_start
            hours.break_end = break_end
            hours.is_deleted = False
            hours.deleted_at = None
            hours.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Special Days
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('schedules', 'special_days')
@htmx_view('schedules/pages/special_days.html', 'schedules/partials/special_days_content.html')
def special_days(request):
    """List all special days/holidays."""
    hub = _hub_id(request)

    special_days_list = SpecialDay.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('date')

    overrides = ScheduleOverride.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('-start_date')

    return {
        'special_days': special_days_list,
        'overrides': overrides,
    }


@require_http_methods(["POST"])
@login_required
def add_special_day(request):
    """Create a new special day."""
    hub = _hub_id(request)

    try:
        data = json.loads(request.body)

        special = SpecialDay(
            hub_id=hub,
            date=data.get('date'),
            name=data.get('name', ''),
            is_closed=data.get('is_closed', True),
            open_time=data.get('open_time') or None,
            close_time=data.get('close_time') or None,
            recurring_yearly=data.get('recurring_yearly', False),
            notes=data.get('notes', ''),
        )
        special.full_clean()
        special.save()

        return JsonResponse({
            'success': True,
            'id': str(special.id),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def edit_special_day(request, pk):
    """Update an existing special day."""
    hub = _hub_id(request)

    try:
        special = get_object_or_404(
            SpecialDay, id=pk, hub_id=hub, is_deleted=False,
        )
        data = json.loads(request.body)

        special.date = data.get('date', special.date)
        special.name = data.get('name', special.name)
        special.is_closed = data.get('is_closed', special.is_closed)
        special.open_time = data.get('open_time') or None
        special.close_time = data.get('close_time') or None
        special.recurring_yearly = data.get('recurring_yearly', special.recurring_yearly)
        special.notes = data.get('notes', special.notes)
        special.full_clean()
        special.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def delete_special_day(request, pk):
    """Soft-delete a special day."""
    hub = _hub_id(request)

    special = get_object_or_404(
        SpecialDay, id=pk, hub_id=hub, is_deleted=False,
    )
    try:
        special.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Is Open Now (API)
# ============================================================================

@require_http_methods(["GET"])
@login_required
def is_open_now(request):
    """API endpoint returning current open/close status."""
    hub = _hub_id(request)
    today = timezone.localdate()
    now_time = timezone.localtime().time()
    today_weekday = today.weekday()

    status = {
        'is_open': False,
        'reason': '',
        'today': str(today),
        'current_time': now_time.strftime('%H:%M'),
    }

    # Check schedule override first (highest priority)
    override = ScheduleOverride.objects.filter(
        hub_id=hub, is_deleted=False,
        start_date__lte=today, end_date__gte=today,
    ).first()
    if override:
        if override.is_closed:
            status['reason'] = str(override.reason)
            return JsonResponse(status)
        elif override.open_time and override.close_time:
            status['is_open'] = override.open_time <= now_time < override.close_time
            status['reason'] = str(override.reason)
            return JsonResponse(status)

    # Check special day (second priority)
    special = SpecialDay.objects.filter(
        hub_id=hub, is_deleted=False, date=today,
    ).first()
    if special:
        if special.is_closed:
            status['reason'] = str(special.name)
            return JsonResponse(status)
        elif special.open_time and special.close_time:
            status['is_open'] = special.open_time <= now_time < special.close_time
            status['reason'] = str(special.name)
            return JsonResponse(status)

    # Check recurring special days
    recurring = SpecialDay.objects.filter(
        hub_id=hub, is_deleted=False,
        recurring_yearly=True,
        date__month=today.month,
        date__day=today.day,
    ).first()
    if recurring:
        if recurring.is_closed:
            status['reason'] = str(recurring.name)
            return JsonResponse(status)
        elif recurring.open_time and recurring.close_time:
            status['is_open'] = recurring.open_time <= now_time < recurring.close_time
            status['reason'] = str(recurring.name)
            return JsonResponse(status)

    # Fall back to regular business hours
    try:
        hours = BusinessHours.objects.get(
            hub_id=hub, is_deleted=False, day_of_week=today_weekday,
        )
        status['is_open'] = hours.is_open_at(now_time)
        if hours.is_closed:
            status['reason'] = _('Closed today')
        elif status['is_open']:
            status['reason'] = _('Regular hours')
        else:
            status['reason'] = _('Outside business hours')
    except BusinessHours.DoesNotExist:
        status['reason'] = _('No hours configured')

    return JsonResponse(status)


# ============================================================================
# Settings
# ============================================================================

@require_http_methods(["GET"])
@login_required
@permission_required('schedules.manage_settings')
@with_module_nav('schedules', 'settings')
@htmx_view('schedules/pages/settings.html', 'schedules/partials/settings_content.html')
def settings_view(request):
    """Show schedule settings."""
    hub = _hub_id(request)
    settings = ScheduleSettings.get_settings(hub)
    settings_form = ScheduleSettingsForm(instance=settings)

    return {
        'config': settings,
        'settings_form': settings_form,
    }


@require_http_methods(["POST"])
@login_required
@permission_required('schedules.manage_settings')
def settings_save(request):
    """Save schedule settings."""
    hub = _hub_id(request)

    try:
        data = json.loads(request.body)
        settings = ScheduleSettings.get_settings(hub)

        settings.timezone = data.get('timezone', settings.timezone)
        settings.week_starts_on = int(data.get('week_starts_on', settings.week_starts_on))
        settings.slot_duration = int(data.get('slot_duration', settings.slot_duration))
        settings.auto_close_enabled = data.get('auto_close_enabled', settings.auto_close_enabled)
        settings.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
