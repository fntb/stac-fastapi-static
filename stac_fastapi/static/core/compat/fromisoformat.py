import datetime as datetimelib


def fromisoformat(datetime_s: str | datetimelib.datetime) -> datetimelib.datetime:
    if isinstance(datetime_s, str):
        if not datetime_s.endswith("Z"):
            return datetimelib.datetime.fromisoformat(datetime_s)
        else:
            return datetimelib.datetime.fromisoformat(datetime_s.rstrip("Z") + "+00:00")
    elif isinstance(datetime_s, datetimelib.datetime):
        return datetime_s
    else:
        raise TypeError(f"{str(datetime_s)} is not a datetime string")
