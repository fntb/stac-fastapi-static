
import datetime as datetimelib


class rfc3339:

    @classmethod
    def datetime_to_str(cls, datetime: datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]) -> str:
        if datetime is None:
            datetime_str = ""
        elif isinstance(datetime, datetimelib.datetime):
            datetime_str = datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif datetime == (None, None):
            datetime_str = ""
        elif datetime[0] == None:
            datetime_str = f"../{cls.datetime_to_str(datetime[1])}"
        elif datetime[1] == None:
            datetime_str = f"{cls.datetime_to_str(datetime[0])}/.."
        elif datetime[0] == datetime[1]:
            datetime_str = cls.datetime_to_str(datetime[1])
        else:
            datetime_str = f"{cls.datetime_to_str(datetime[0])}/{cls.datetime_to_str(datetime[1])}"

        return datetime_str
