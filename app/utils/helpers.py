from datetime import datetime
import json


def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def calculate_age(birthdate):
    """Calculate age from birthdate"""
    if birthdate:
        today = datetime.today()
        return (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
        )
    return None


def get_race_status_class(status):
    """Get Bootstrap class for race status"""
    status_classes = {
        "open": "success",
        "in_progress": "warning",
        "completed": "info",
        "cancelled": "danger",
    }
    return status_classes.get(status, "secondary")


def format_duration(start_time, end_time):
    """Calculate and format duration between two timestamps"""
    if start_time and end_time:
        duration = end_time - start_time
        total_seconds = duration.total_seconds()
        return format_time(total_seconds)
    return "--:--:--"


def get_age_group(birth_date, age_groups_json):
    if not birth_date or not age_groups_json:
        return "Unknown"
    try:
        age_groups = json.loads(age_groups_json)
    except json.JSONDecodeError:
        return "Unknown"

    today = datetime.date.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )

    for group in age_groups:
        if group["min"] <= age <= group["max"]:
            return group["label"]
    return "Other"
