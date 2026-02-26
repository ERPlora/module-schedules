"""AI tools for the Schedules module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class GetBusinessHours(AssistantTool):
    name = "get_business_hours"
    description = "Get the configured business hours for each day of the week."
    module_id = "schedules"
    required_permission = "schedules.view_businesshours"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from schedules.models import BusinessHours
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = BusinessHours.objects.all().order_by('day_of_week')
        return {
            "business_hours": [
                {
                    "day": days[h.day_of_week] if h.day_of_week < 7 else str(h.day_of_week),
                    "is_closed": h.is_closed,
                    "open_time": str(h.open_time) if h.open_time else None,
                    "close_time": str(h.close_time) if h.close_time else None,
                    "break_start": str(h.break_start) if h.break_start else None,
                    "break_end": str(h.break_end) if h.break_end else None,
                }
                for h in hours
            ]
        }


@register_tool
class ListSpecialDays(AssistantTool):
    name = "list_special_days"
    description = "List upcoming special days (holidays, closures)."
    module_id = "schedules"
    required_permission = "schedules.view_businesshours"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from datetime import date
        from schedules.models import SpecialDay
        upcoming = SpecialDay.objects.filter(date__gte=date.today()).order_by('date')[:20]
        return {
            "special_days": [
                {
                    "date": str(sd.date),
                    "name": sd.name,
                    "is_closed": sd.is_closed,
                    "notes": sd.notes,
                }
                for sd in upcoming
            ]
        }
