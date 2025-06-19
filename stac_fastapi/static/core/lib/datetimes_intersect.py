
import datetime as datetimelib


def _intersect_datetime_and_datetimes(
        datetime: datetimelib.datetime,
        datetimes: tuple[datetimelib.datetime | None, datetimelib.datetime | None]
) -> bool:
    return (datetimes[0] is None or datetime >= datetimes[0]) and (datetimes[1] is None or datetime <= datetimes[1])


def _intersect_datetimes(
    datetimes_a: tuple[datetimelib.datetime | None, datetimelib.datetime | None],
    datetimes_b: tuple[datetimelib.datetime | None, datetimelib.datetime | None]
) -> bool:
    return (
        datetimes_a[0] is None or datetimes_b[1] is None or datetimes_a[0] <= datetimes_b[1]
    ) and (
        datetimes_a[1] is None or datetimes_b[0] is None or datetimes_a[1] >= datetimes_b[0]
    )


def datetimes_intersect(
        a: tuple[datetimelib.datetime | None, datetimelib.datetime | None] | datetimelib.datetime,
        b: tuple[datetimelib.datetime | None, datetimelib.datetime | None] | datetimelib.datetime
) -> bool:
    if isinstance(a, datetimelib.datetime) and isinstance(b, datetimelib.datetime):
        return a == b
    elif isinstance(a, datetimelib.datetime):
        return _intersect_datetime_and_datetimes(a, b)
    elif isinstance(b, datetimelib.datetime):
        return _intersect_datetime_and_datetimes(b, a)
    else:
        return _intersect_datetimes(a, b)
