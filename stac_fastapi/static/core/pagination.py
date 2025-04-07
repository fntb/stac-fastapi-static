from __future__ import annotations

from typing import (
    Optional,
    NamedTuple,
    Iterator,
    Iterable,
    Literal
)

from collections import deque

from .walk import WalkPath
from .walk import WalkResult


class WalkMarker(WalkPath):
    direction: Literal["next", "prev"]

    def __new__(cls, *args, direction: Literal["next", "prev"], **kwargs):
        return WalkPath.__new__(cls, *args, **kwargs)

    def __init__(self, o: Iterable, *, direction: Literal["next", "prev"]):
        self.direction = direction

    @property
    def is_start(self) -> bool:
        return self.direction == "next"

    @property
    def is_end(self) -> bool:
        return self.direction == "prev"

    @property
    def start(self) -> WalkPath | None:
        return WalkPath(self) if self.is_start else None

    @property
    def end(self) -> WalkPath | None:
        return WalkPath(self) if self.is_end else None

    @classmethod
    def from_str(cls, walk_path_s: str):

        try:
            [direction, walk_path] = walk_path_s.split(":")

            if direction not in ("next", "prev"):
                raise ValueError("Token direction must be 'next' or 'prev'")

            walk_path = WalkPath.from_str(walk_path)

            return WalkMarker(walk_path, direction=direction)
        except Exception as error:
            raise ValueError(f"Invalid Token : {walk_path_s}") from error

    def __str__(self):
        return f"{self.direction}:{str(WalkPath(self))}"

    def __repr__(self):
        return "WalkMarker.from_str(" + str(self) + ")"


class WalkPage(NamedTuple):
    page: list[WalkResult] = []

    prev: Optional[WalkMarker] = None
    next: Optional[WalkMarker] = None

    @classmethod
    def _first(
        cls,
        walk: Iterator[WalkResult],
        page_len: int = 10,
    ) -> WalkPage:
        buffer: list[WalkResult] = []

        is_last_page = True

        for walk_result in walk:
            if len(buffer) < page_len:
                buffer.append(walk_result)
            else:
                is_last_page = False
                break

        prev: Optional[WalkPath] = None
        next: Optional[WalkPath] = None

        if not is_last_page:
            next = buffer[-1].walk_path

        return cls(
            page=buffer,
            next=WalkMarker(next, direction="next") if next else None,
        )

    @classmethod
    def _next(
            cls,
            walk: Iterator[WalkResult],
            page_start: WalkPath,
            page_len: int = 10,
    ) -> WalkPage:
        buffer: list[WalkResult] = []

        is_last_page = True

        for walk_result in walk:
            if page_start is None or walk_result.walk_path >= page_start:
                if len(buffer) <= page_len:
                    buffer.append(walk_result)
                else:
                    is_last_page = False
                    break
            else:
                continue

        prev: Optional[WalkPath] = None
        next: Optional[WalkPath] = None

        if len(buffer) == 0:
            prev = WalkPath.max
        else:
            if is_last_page:
                prev = buffer.pop(0).walk_path
            else:
                prev = buffer.pop(0).walk_path
                if len(buffer) > 0:
                    next = buffer[-1].walk_path

        return cls(
            page=buffer,
            prev=WalkMarker(prev, direction="prev") if prev else None,
            next=WalkMarker(next, direction="next") if next else None,
        )

    @classmethod
    def _prev(
            cls,
            walk: Iterator[WalkResult],
            page_end: WalkPath,
            page_len: int = 10,
    ) -> WalkPage:
        buffer: deque[WalkResult] = deque(maxlen=page_len + 1)

        is_first_page = True

        for walk_result in walk:
            if walk_result.walk_path <= page_end:
                if len(buffer) > page_len:
                    is_first_page = False
                buffer.append(walk_result)
            else:
                break

        prev: Optional[WalkPath] = None
        next: Optional[WalkPath] = None

        if len(buffer) == 0:
            next = WalkPath.min
        else:
            if is_first_page:
                next = buffer[-1].walk_path
            else:
                prev = buffer.popleft().walk_path
                if len(buffer) > 0:
                    next = buffer[-1].walk_path

        return cls(
            page=list(buffer),
            prev=WalkMarker(prev, direction="prev") if prev else None,
            next=WalkMarker(next, direction="next") if next else None,
        )

    @classmethod
    def paginate(
            cls,
            walk: Iterator[WalkResult],
            walk_marker: Optional[WalkMarker | str] = None,
            len: int = 10,
    ):
        if isinstance(walk_marker, str):
            walk_marker = WalkMarker.from_str(walk_marker)

        if walk_marker is None:
            return cls._first(walk, len)
        elif walk_marker.is_end:
            return cls._prev(
                walk,
                walk_marker,
                len
            )
        else:
            return cls._next(
                walk,
                walk_marker,
                len
            )
