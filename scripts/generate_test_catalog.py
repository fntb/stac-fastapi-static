import argparse
from typing import Optional
from os import path

import pystac

from stac_test_tools import TestCatalog

parser = argparse.ArgumentParser()
parser.add_argument("n_items", type=int, metavar="n-items", help="Approximate number of items to generate")
parser.add_argument(
    "-o", "--output-dir",
    help="Output directory for the generated catalog, defaults to ./stac_test_catalogs/<n_items>/",
)

args = parser.parse_args()

n_items: int = args.n_items
output_dir: Optional[str] = args.output_dir

if output_dir:
    catalog_href = path.abspath(path.join(output_dir, "catalog.json"))
else:
    catalog_href = path.abspath(path.join("stac_test_catalogs", str(n_items), "catalog.json"))

i_items = 0
i_others = 0
for generated_object in TestCatalog.generate(n_items=n_items, catalog_href=catalog_href):
    if isinstance(generated_object, pystac.Item):
        i_items += 1
    else:
        i_others += 1

    print(f"\rgenerated={i_items}(/{n_items}) +{i_others}", end="")

print("\r", end="")
