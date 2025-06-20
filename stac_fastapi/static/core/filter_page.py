
from typing import (
    Optional,
)

from .walk import (
    WalkResult,
    SkipWalk,
    WalkPath,
)


def match_pagination(
    walk_path: WalkPath,
    start: Optional[WalkPath] = None,
    end: Optional[WalkPath] = None,
) -> tuple[bool, bool]:
    if end is not None and walk_path > end:
        return (False, False)
    elif start is not None and walk_path < start:
        if start in walk_path:
            return (False, True)
        else:
            return (False, False)
    else:
        return (True, True)


def make_filter_page(
    start: Optional[WalkPath] = None,
    end: Optional[WalkPath] = None,
):
    def filter_page(walk_result: WalkResult) -> bool:
        (matches, sub_matches) = match_pagination(walk_result.walk_path, start, end)
        if matches:
            return True
        elif sub_matches:
            return False
        else:
            raise SkipWalk

    return filter_page
