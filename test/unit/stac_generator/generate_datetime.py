from typing import (
    Optional
)
import random
import datetime as datetimelib


def generate_start_end_datetime(
    restriction: Optional[tuple[datetimelib.datetime,
                                datetimelib.datetime]] | None = None,
    duration: Optional[datetimelib.timedelta] | None = None
) -> tuple[datetimelib.datetime, datetimelib.datetime]:
    if not duration:
        return tuple(
            sorted([
                generate_datetime(restriction),
                generate_datetime(restriction)
            ])
        )
    else:
        start_datetime = generate_datetime(restriction)
        end_datetime = datetimelib.datetime.fromtimestamp(
            start_datetime.timestamp() + duration.total_seconds(),
            tz=restriction[0].tzinfo if restriction else None
        )

        if restriction:
            end_datetime = min(end_datetime, restriction[1])

        return (start_datetime, end_datetime)


def generate_datetime(
    restriction: Optional[tuple[datetimelib.datetime,
                                datetimelib.datetime]] | None = None
) -> datetimelib.datetime:
    start_timestamp = restriction[0].timestamp() if restriction else 0
    end_timestamp = restriction[1].timestamp(
    ) if restriction else datetimelib.datetime.now().timestamp()

    return datetimelib.datetime.fromtimestamp(
        start_timestamp + random.random() * (end_timestamp - start_timestamp),
        tz=restriction[0].tzinfo if restriction else None
    )
