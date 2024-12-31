import os
from dotenv import load_dotenv
from pytz import timezone, UnknownTimeZoneError
from flask import current_app
from datetime import datetime

load_dotenv()

TIMEZONE = os.environ.get("TIMEZONE")


def get_timezone():
    try:
        return timezone(TIMEZONE) # type: ignore
    except UnknownTimeZoneError:
        # Handle error, log it, and return a default timezone
        return timezone('UTC')


def now_tz():
    return datetime.now(get_timezone())


def convert_to_local(dt):
    local_tz = get_timezone()
    return dt.astimezone(local_tz)


if __name__ == '__main__':
    print(get_timezone())