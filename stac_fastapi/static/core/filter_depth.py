
from typing import (
    Optional,
)

from .walk import (
    WalkResult,
    SkipWalk,
)


def make_filter_depth(depth: Optional[int] = 0):

    def filter_depth(walk_result: WalkResult) -> bool:
        if len(walk_result.walk_path) > depth + 1:
            raise SkipWalk
        else:
            return True

    return filter_depth
