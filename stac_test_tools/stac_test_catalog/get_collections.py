from typing import (
    Iterator,
    NamedTuple
)

import pystac


# class WalkedCollection(NamedTuple):
#     collection: pystac.Collection
#     walk: list[pystac.Catalog | pystac.Collection]


def get_collections(catalog: pystac.Catalog) -> Iterator[pystac.Collection]:
    if not isinstance(catalog, (pystac.Catalog, pystac.Collection)):
        raise TypeError("Not a STAC Catalog")

    if isinstance(catalog, pystac.Collection):
        yield catalog

    for child in catalog.get_children():
        yield from get_collections(child)

# def walk_collections(catalog: pystac.Catalog, _walk: list[pystac.Catalog | pystac.Collection] = []) -> Iterator[WalkedCollection]:
#     if not isinstance(catalog, (pystac.Catalog, pystac.Collection)):
#         raise TypeError("Not a STAC Catalog")

#     _walk += [catalog]

#     if isinstance(catalog, pystac.Collection):
#         yield WalkedCollection(
#             collection=catalog,
#             walk=_walk
#         )

#     for child in catalog.get_children():
#         yield from walk_collections(child, _walk)
