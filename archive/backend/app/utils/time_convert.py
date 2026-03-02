from datetime import datetime, timezone, timedelta


def convert(timestamp):
    # PST = UTC-8
    pst = timezone(timedelta(hours=-8))

    # Convert to datetime, mind millisecond
    dt = datetime.fromtimestamp(timestamp / 1000, tz=pst)
    # ISO format
    iso_str = dt.isoformat()

    return iso_str
