from typing import Optional

import argparse
import os

import pystac

parser = argparse.ArgumentParser()
parser.add_argument("catalog_href", type=str, metavar="catalog-href", help="Catalog to clone")
parser.add_argument("catalog_name", type=str, metavar="catalog-name", help="Name of the created catalog directory")
parser.add_argument(
    "-o", "--catalog-dir",
    help="Output directory for the generated catalog, defaults to ./test_catalogs/<catalog-name>/",
)

args = parser.parse_args()

catalog_href: str = args.catalog_href
catalog_name: str = args.catalog_name
catalog_dir: Optional[str] = args.catalog_dir

if catalog_dir:
    catalog_file = os.path.abspath(os.path.join(catalog_dir, catalog_name, "catalog.json"))
else:
    catalog_file = os.path.abspath(os.path.join("test_catalogs", catalog_name, "catalog.json"))


catalog = pystac.Catalog.from_file(catalog_href)


def resolve_partial_catalog(catalog: pystac.Catalog | pystac.Collection | pystac.Item):
    n_items = 0
    n_children = 0

    skipped_links = []

    for link in catalog.links:
        if link.rel == "item":
            if n_items <= 10:
                link.resolve_stac_object(catalog.get_root()).target
                n_items += 1
            else:
                skipped_links.append(link)
        elif link.rel == "child":
            if n_children <= 5:
                resolve_partial_catalog(link.resolve_stac_object(catalog.get_root()).target)
                n_children += 1
            else:
                skipped_links.append(link)

    for skipped_link in skipped_links:
        catalog.links.remove(skipped_link)


resolve_partial_catalog(catalog)

catalog.normalize_and_save(catalog_file, skip_unresolved=True)
