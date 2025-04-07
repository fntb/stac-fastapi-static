
from typing import (
    Iterator,
    Callable,
    Optional
)

from ..walk import (
    WalkResult,
    SkipWalk,
    WalkPath
)

from .walk_filter import make_walk_filter, make_walk_filter_factory


def make_match_pagination(
    start: Optional[WalkPath] = None,
    end: Optional[WalkPath] = None,
) -> Callable[[WalkPath], tuple[bool, bool]]:

    def match(walk_path: WalkPath) -> tuple[bool, bool]:
        if end is not None and walk_path > end:
            return (False, False)
        elif start is not None and walk_path < start:
            if start in walk_path:
                return (False, True)
            else:
                return (False, False)
        else:
            return (True, True)

    return match


def make_pagination_filter(
    start: Optional[WalkPath] = None,
    end: Optional[WalkPath] = None,
) -> Callable[[WalkResult], bool]:

    match_pagination = make_match_pagination(
        start=start,
        end=end
    )

    def filter(walk_result: WalkResult) -> bool:
        (matches, sub_matches) = match_pagination(walk_result.walk_path)
        if matches:
            return True
        elif sub_matches:
            return False
        else:
            raise SkipWalk

    return filter


make_walk_pagination_filter = make_walk_filter_factory(make_pagination_filter)
