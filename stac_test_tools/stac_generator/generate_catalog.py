from typing import (
    Callable,
    Generator
)
import math

import pystac

from .generate_id import generate_id
from .generate_text import generate_title_and_description_props
from .generate_item import generate_item
from .generate_collection import generate_collection


def generate_catalog_from_shape(
    shape: tuple[int, int] | Callable[[int], tuple[int, int]] = (1, 0),
) -> Generator[pystac.Item | pystac.Collection, None, pystac.Catalog]:
    title_and_description = generate_title_and_description_props()

    catalog = pystac.Catalog(
        generate_id(),
        title_and_description["description"],
        title=title_and_description["title"]
    )

    yield catalog

    (item_count, child_count) = shape if isinstance(
        shape, (tuple, list)) else shape(1)

    for _ in range(item_count):
        yield (item := generate_item())

        catalog.add_item(item)

    for _ in range(child_count):
        collection = yield from generate_collection(
            shape,
            _current_depth=2
        )

        yield collection

        catalog.add_child(collection)

        # generated = generate_collection(
        #     shape,
        #     _current_depth=2
        # )

        # collection = next(generated)

        # yield collection

        # catalog.add_child(collection)

        # yield from generated

    return catalog


def make_default_shape(n_items: int = 100):
    n = n_items
    i = n_items_per_collection = 25
    c = n_sub_collections_per_collection = 5

    depth = math.log(1 - n * (1 - c) / i) / math.log(c) - 1

    def shape(current_depth: int):
        if current_depth <= depth:
            return (i, c)
        else:
            return (i, 0)

    return shape


def generate_catalog(
    n_items: int = 100,
) -> Generator[pystac.Item | pystac.Collection, None, pystac.Catalog]:
    return generate_catalog_from_shape(make_default_shape(n_items))
