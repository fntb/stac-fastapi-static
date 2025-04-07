
from typing import (
    Iterator,
    NamedTuple
)

import pystac


def get_items(catalog: pystac.Catalog) -> Iterator[pystac.Item]:
    if isinstance(catalog, pystac.Item):
        yield catalog
    else:
        for item in catalog.get_items(recursive=False):
            yield item

        for child in catalog.get_children():
            yield from get_items(child)

# class WalkedItem(NamedTuple):
#     item: pystac.Item
#     walk: list[pystac.Catalog | pystac.Collection | pystac.Item]

# def walk_items(catalog: pystac.Catalog, _walk: list[pystac.Catalog | pystac.Collection] = []) -> Iterator[WalkedItem]:
#     _walk += [catalog]

#     if isinstance(catalog, pystac.Item):
#         yield WalkedItem(
#             item=catalog,
#             walk=_walk
#         )
#     else:
#         for item in catalog.get_items(recursive=False):
#             yield from walk_items(item, _walk=_walk)

#         for child in catalog.get_children():
#             yield from walk_items(child, _walk=_walk)
