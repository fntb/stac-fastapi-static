
from typing import (
    Iterator,
    Callable,
    TypeVar,
    Any,
    cast,
    ParamSpec
)

from ..walk import (
    WalkResult,
    BadWalkResultError,
    SkipWalk,
    logger as walk_logger
)


def backraise_skip_walk(
    walk: Iterator[WalkResult],
):
    try:
        none = walk.throw(SkipWalk)

        if none is not None:
            walk_logger.error(f"Exception descent yielded a walk result, it will be silently swallowed and inconsistencies will arise. This error is probably due to an incompatible walk filter implementation.", extra={
                "walk_result": none
            })

        assert none == None
    except StopIteration:
        return


def chain_walk_filters(*walk_filters: Callable[[Iterator[WalkResult]], Iterator[WalkResult]]):

    def walk_filter_chain(walk: Iterator[WalkResult]) -> Iterator[WalkResult]:
        filtered_walk = walk
        for walk_filter in walk_filters:
            filtered_walk = walk_filter(filtered_walk)

        for walk_result in filtered_walk:
            try:
                yield walk_result
            except SkipWalk:
                yield None

                backraise_skip_walk(filtered_walk)

    return walk_filter_chain


def make_walk_filter(
    walk_result_filter: Callable[[WalkResult], bool | WalkResult | None]
) -> Callable[[Iterator[WalkResult]], Iterator[WalkResult]]:

    def walk_filter(walk: Iterator[WalkResult]) -> Iterator[WalkResult]:
        for walk_result in walk:
            try:
                filtered_walk_result = walk_result_filter(walk_result)

                try:
                    if filtered_walk_result == True:
                        yield walk_result
                    elif filtered_walk_result not in (None, False):
                        yield filtered_walk_result

                except SkipWalk:
                    yield None
                    raise SkipWalk

            except BadWalkResultError as error:
                walk_logger.warning(f"Skipping walk_result {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                continue
            except SkipWalk:
                backraise_skip_walk(walk)

    return walk_filter


WalkResultFilterFactoryParams = ParamSpec("WalkResultFilterFactoryParams")


def make_walk_filter_factory(make_walk_result_filter: Callable[WalkResultFilterFactoryParams, Callable[[WalkResult], bool | WalkResult | None]]) -> Callable[[Iterator[WalkResult]], Iterator[WalkResult]]:

    def _make_walk_filter(
        *args: WalkResultFilterFactoryParams.args,
        **kwargs: WalkResultFilterFactoryParams.kwargs
    ):

        return make_walk_filter(make_walk_result_filter(*args, **kwargs))

    return cast(
        Callable[WalkResultFilterFactoryParams, Callable[[Iterator[WalkResult]], Iterator[WalkResult]]],
        _make_walk_filter
    )
