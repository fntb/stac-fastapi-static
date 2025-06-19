from typing import (
    List,
)

from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog
from stac_pydantic.item import Item
from stac_pydantic.links import Link
from stac_pydantic.shared import MimeTypes


from ..errors import (
    BadStacObjectError
)


def get_item_hrefs(walkable: Catalog | Collection) -> List[str]:

    return [
        link.href
        for link
        in walkable.links.link_iterator()
        if link.rel == "item"
    ]


def get_child_hrefs(walkable: Catalog | Collection) -> List[str]:

    return [
        link.href
        for link
        in walkable.links.link_iterator()
        if link.rel == "child"
    ]


def get_self_href(stac_object: Item | Collection | Catalog) -> str:
    for link in stac_object.links.link_iterator():
        if link.rel == "self":
            return link.href

    raise BadStacObjectError("Bad STAC Object - Missing 'self' link", object=stac_object)


def set_self_href(stac_object: Item | Collection | Catalog, href: str):
    for link in stac_object.links.link_iterator():
        if link.rel == "self":
            link.href = href
            break
    else:
        stac_object.links.append(
            Link(
                href=href,
                rel="self",
                type=MimeTypes.geojson.value
            )
        )
