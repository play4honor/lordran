import datetime


def get_utc_offset(local_time: datetime.time):

    hour_diff = local_time.hour - datetime.datetime.utcnow().hour

    if hour_diff > 12:
        hour_diff = hour_diff - 24
    elif hour_diff < -12:
        hour_diff = hour_diff + 24

    return hour_diff


def get_time_response(res):

    try:
        tm = datetime.time.fromisoformat(res)
    except ValueError:
        tm = None

    return tm
