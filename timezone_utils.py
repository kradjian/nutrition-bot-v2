"""Timezone utilities for handling user-specific time"""

from datetime import datetime, timedelta
from typing import Optional
import pytz

# Common timezone mappings for user-friendly input
TIMEZONE_ALIASES = {
    # Russia
    'мск': 'Europe/Moscow',
    'msk': 'Europe/Moscow',
    'москва': 'Europe/Moscow',
    'moscow': 'Europe/Moscow',
    'спб': 'Europe/Moscow',
    'питер': 'Europe/Moscow',
    
    # UAE / Dubai
    'дубай': 'Asia/Dubai',
    'dubai': 'Asia/Dubai',
    'dubay': 'Asia/Dubai',
    'dxb': 'Asia/Dubai',
    'uae': 'Asia/Dubai',
    'оаэ': 'Asia/Dubai',
    
    # Kazakhstan
    'алматы': 'Asia/Almaty',
    'almaty': 'Asia/Almaty',
    'астана': 'Asia/Almaty',
    'astana': 'Asia/Almaty',
    
    # Common
    'utc': 'UTC',
    'gmt': 'UTC',
    'лондон': 'Europe/London',
    'london': 'Europe/London',
    'нью-йорк': 'America/New_York',
    'new_york': 'America/New_York',
    'ny': 'America/New_York',
    'токио': 'Asia/Tokyo',
    'tokyo': 'Asia/Tokyo',
}


def normalize_timezone(tz_input: str) -> str:
    """Convert user-friendly timezone to IANA timezone"""
    tz_lower = tz_input.lower().strip()
    
    # Check aliases
    if tz_lower in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[tz_lower]
    
    # Check if it's already a valid timezone
    try:
        pytz.timezone(tz_input)
        return tz_input
    except pytz.UnknownTimeZoneError:
        pass
    
    # Default to UTC if unknown
    return 'UTC'


def get_current_date_for_user(timezone: str, day_end_hour: int = 4) -> str:
    """
    Get the current 'logical date' for a user.
    
    If day_end_hour=4, then:
    - 2024-01-15 03:00 → still "2024-01-14" (yesterday's date)
    - 2024-01-15 04:00 → "2024-01-15" (today's date)
    
    Args:
        timezone: IANA timezone name (e.g., 'Europe/Moscow')
        day_end_hour: Hour when the day "ends" (0-23)
    
    Returns:
        Date string in format 'YYYY-MM-DD'
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    
    # If current hour is before day_end_hour, it's still "yesterday"
    if now.hour < day_end_hour:
        yesterday = now - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    return now.strftime('%Y-%m-%d')


def get_user_now(timezone: str) -> datetime:
    """Get current datetime in user's timezone"""
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def format_datetime(dt: datetime, timezone: str, fmt: str = '%H:%M') -> str:
    """Format datetime in user's timezone"""
    tz = pytz.timezone(timezone)
    local_dt = dt.astimezone(tz)
    return local_dt.strftime(fmt)


def get_relative_date(
    relative_to: str,
    timezone: str,
    day_end_hour: int = 4
) -> str:
    """
    Get date relative to user's "today"
    
    Args:
        relative_to: 'today', 'yesterday', 'tomorrow'
        timezone: IANA timezone name
        day_end_hour: Hour when day ends
    
    Returns:
        Date string 'YYYY-MM-DD'
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    
    # Determine "logical today"
    if now.hour < day_end_hour:
        logical_today = now - timedelta(days=1)
    else:
        logical_today = now
    
    if relative_to == 'today':
        return logical_today.strftime('%Y-%m-%d')
    elif relative_to == 'yesterday':
        yesterday = logical_today - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    elif relative_to == 'tomorrow':
        tomorrow = logical_today + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    return logical_today.strftime('%Y-%m-%d')


def get_day_start_end(
    date_str: str,
    timezone: str,
    day_end_hour: int = 4
) -> tuple:
    """
    Get start and end datetime for a logical day
    
    Returns:
        (start_datetime, end_datetime) in UTC
    """
    tz = pytz.timezone(timezone)
    
    # Parse the date
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Day starts at day_end_hour of previous day
    start_local = tz.localize(date.replace(hour=day_end_hour)) - timedelta(days=1)
    end_local = tz.localize(date.replace(hour=day_end_hour))
    
    # Convert to UTC for database queries
    start_utc = start_local.astimezone(pytz.UTC)
    end_utc = end_local.astimezone(pytz.UTC)
    
    return start_utc, end_utc
