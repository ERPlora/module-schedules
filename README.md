# Schedules Module

Business hours, holiday schedules, and availability management.

## Features

- Define regular weekly business hours per day of week with open and close times
- Support midday break periods within business hours
- Mark specific days of the week as closed
- Manage special days (holidays, events) with optional custom hours or full closure
- Set special days to recur yearly
- Create schedule overrides for temporary changes across date ranges (e.g., extended holiday hours)
- Configurable timezone, week start day, and time slot duration
- Automatic time slot generation based on business hours and break periods
- Check if the business is open at any given time
- Validation for time ranges (open before close, breaks within business hours)
- Optional auto-close after closing time

## Installation

This module is installed automatically via the ERPlora Marketplace.

## Configuration

Access settings via: **Menu > Schedules > Settings**

Configurable options include:

- Timezone (IANA format, e.g., Europe/Madrid)
- Week start day
- Default time slot duration (minutes)
- Auto-close after closing time

## Usage

Access via: **Menu > Schedules**

### Views

| View | URL | Description |
|------|-----|-------------|
| Hours | `/m/schedules/dashboard/` | Manage regular weekly business hours |
| Special Days | `/m/schedules/special_days/` | Manage holidays and special schedule days |
| Settings | `/m/schedules/settings/` | Module configuration |

## Models

| Model | Description |
|-------|-------------|
| `ScheduleSettings` | Per-hub configuration for timezone, week start, slot duration, and auto-close |
| `BusinessHours` | Regular weekly hours per day of week with open/close times and optional break period |
| `SpecialDay` | Holiday or special day with date, custom hours or closure, yearly recurrence, and notes |
| `ScheduleOverride` | Temporary schedule change for a date range with reason, custom hours, or full closure |

## Permissions

| Permission | Description |
|------------|-------------|
| `schedules.view_schedule` | View schedules |
| `schedules.add_schedule` | Create schedule entries |
| `schedules.change_schedule` | Edit schedule entries |
| `schedules.delete_schedule` | Delete schedule entries |
| `schedules.manage_settings` | Manage module settings |

## License

MIT

## Author

ERPlora Team - support@erplora.com
