import datetime
import logging
import re

from app.services.logging import setup_logging  # noqa: F401

logger = logging.getLogger(__name__)

months = {
    "січня": "January",
    "лютого": "February",
    "березня": "March",
    "квітня": "April",
    "травня": "May",
    "червня": "June",
    "липня": "July",
    "серпня": "August",
    "вересня": "September",
    "жовтня": "October",
    "листопада": "November",
    "грудня": "December"
}


def parse_relative_date(date_string: str) -> datetime.date:
    now = datetime.datetime.now()

    if "сьогодні" in date_string:
        return now.date()

    if "вчора" in date_string:
        return (now - datetime.timedelta(days=1)).date()

    match = re.match(r"(\d+) дн(?:і|ів|я) (назад|тому)", date_string)
    if match:
        days_ago = int(match.group(1))
        return (now - datetime.timedelta(days=days_ago)).date()

    if "тиждень" in date_string:
        return (now - datetime.timedelta(weeks=1)).date()

    # Handle the absolute date format "dd month" or "dd month yyyy"
    for month_ua, month_en in months.items():
        if month_ua in date_string:
            day_match = re.match(r"(\d{1,2}) " + month_ua, date_string)
            if day_match:
                current_year = now.year
                # Handle full date with year
                if len(date_string.split()) == 3:
                    year_match = re.match(r"\d{4}", date_string.split()[2])
                    if year_match:
                        current_year = int(year_match.group(0))
                day = int(day_match.group(1))
                while True:
                    try:
                        return datetime.date(current_year, list(months.values()).index(month_en) + 1, day)
                    # Real case error: "31 червня 2024"
                    except ValueError as e:
                        if day > 0 and 'day is out of range for month' in e.args[0]:
                            logging.warning(f"Invalid day {day} for month {month_en}. Falling back to {day - 1}...")
                            day -= 1
                        else:
                            return None

    # If none of the patterns matched, return None
    return None
