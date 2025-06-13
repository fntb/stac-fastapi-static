import pystac

catalog = pystac.Catalog.from_file("")


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

catalog.normalize_and_save("", skip_unresolved=True)
