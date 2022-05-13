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
        utc_offset = get_utc_offset(tm)
        prefix = "+" if utc_offset > 0 else ""
        tm_str = f"{prefix}{utc_offset}"
    except ValueError:
        tm_str = None

    return tm_str


def get_time_range(res):

    time_list = [d.strip() for d in res.split(",")]
    try:
        iso_list = [datetime.time.fromisoformat(d) for d in time_list]
    except ValueError:
        return None

    if len(iso_list) != 2 or iso_list[0] >= iso_list[1]:
        return None

    return [str(t) for t in iso_list]


def get_reasonable_hours(res):
    try:
        hrs = int(res)
        if hrs >= 12:
            hrs = None
    except ValueError:
        hrs = None
    return hrs


def get_dates(res):
    date_list = [d.strip() for d in res.split(",")]
    try:
        iso_list = [datetime.date.fromisoformat(d) for d in date_list]
    except ValueError:
        return None

    # mirai
    for d in iso_list:
        if d < datetime.date.today():
            return None

    return [d.isoformat() for d in iso_list]


def get_expiration(res):
    try:
        hrs = int(res)
    except ValueError:
        hrs = None
    return hrs
