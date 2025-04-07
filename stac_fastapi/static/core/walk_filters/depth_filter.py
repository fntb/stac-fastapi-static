
from typing import (
    Iterator,
    Callable,
    Optional
)

from ..walk import (
    WalkResult,
    SkipWalk,
)

from .walk_filter import make_walk_filter, make_walk_filter_factory


def make_depth_filter(
    depth: Optional[int] = 0,
) -> Callable[[WalkResult], bool]:

    if depth > 0:
        def filter(walk_result: WalkResult) -> bool:
            if len(walk_result.walk_path) > depth + 1:
                raise SkipWalk
            else:
                return True
    else:
        def filter(walk_result: WalkResult) -> bool:
            return True

    return filter


make_walk_depth_filter = make_walk_filter_factory(make_depth_filter)
