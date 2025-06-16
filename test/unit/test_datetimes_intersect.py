
import datetime as datetimelib

from stac_fastapi.static.core.lib.datetimes_intersect import datetimes_intersect


def test_datetimes_intersect():
    days = [
        datetimelib.datetime(year=2025, month=6, day=i, tzinfo=datetimelib.timezone.utc)
        for i in range(9, 17)
    ]

    window = (days[2], days[5])

    expected_to_intersect = [
        (days[1], days[3]),
        (days[3], days[4]),
        (days[4], days[6]),
        #
        (None, None),
        (days[0], None),
        (None, days[4]),
        (days[3], None),
        (None, days[7]),
        #
        days[2],
        days[3],
        days[4],
        days[5],
    ]

    expected_not_to_intersect = [
        (days[0], days[1]),
        (days[6], days[7]),
        #
        (None, days[1]),
        (days[6], None),
        #
        days[0],
        days[1],
        days[6],
        days[7],
    ]

    for datetimes in expected_to_intersect:
        assert datetimes_intersect(window, datetimes)

    for datetimes in expected_not_to_intersect:
        assert not datetimes_intersect(window, datetimes)
