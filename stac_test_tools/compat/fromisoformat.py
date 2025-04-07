import datetime as datetimelib


def fromisoformat(datetime_s: str) -> datetimelib.datetime:
    if not datetime_s.endswith("Z"):
        return datetimelib.datetime.fromisoformat(datetime_s)
    else:
        return datetimelib.datetime.fromisoformat(datetime_s.rstrip("Z") + "+00:00")
