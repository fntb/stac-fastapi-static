from typing import Optional, Tuple

import argparse
import os

import pystac
import pystac.errors

parser = argparse.ArgumentParser()
parser.add_argument("catalog_href", type=str, metavar="catalog-href", help="Catalog to size up")

args = parser.parse_args()

catalog_href: str = args.catalog_href

for cls in (pystac.Catalog, pystac.Collection):
    try:
        catalog = cls.from_file(catalog_href)
        break
    except pystac.STACTypeError:
        pass
else:
    raise ValueError(f"{catalog_href} is not a valid Catalog or Collection")


def size_catalog(catalog: pystac.Catalog | pystac.Collection | pystac.Item) -> Tuple[int, int]:
    n_items = 0
    n_children = 0

    for link in catalog.links:
        if link.rel == "item":
            n_items += 1
        elif link.rel == "child":
            n_children += 1
            (child_n_items, child_n_grandchildren) = size_catalog(link.resolve_stac_object(catalog.get_root()).target)
            n_items += child_n_items
            n_children += child_n_grandchildren

    return (n_items, n_children)


(n_items, n_children) = size_catalog(catalog)

print(f"{n_items=}")
print(f"{n_children=}")
