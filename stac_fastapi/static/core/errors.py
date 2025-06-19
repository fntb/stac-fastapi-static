
from typing import (
    Optional
)

from stac_pydantic import (
    Item,
    Collection,
    Catalog
)


def _get_self_href(stac_object: Item | Collection | Catalog) -> str:
    for link in stac_object.links.link_iterator():
        if link.rel == "self":
            return link.href

    raise ValueError("Self href not found")


class BadStacObjectError(ValueError):

    def __init__(
        self,
        message,
        *args,
        href: Optional[str] = None,
        id: Optional[str] = None,
        object: Optional[Item | Collection | Catalog] = None,
        **kwargs
    ):

        # if href:
        #     id = id or guess_id_from_href(href)

        if object:
            try:
                id = id or object.id
            except Exception:
                pass

            try:
                href = href or _get_self_href(object)
            except Exception:
                pass

            # if href:
            #     id = id or guess_id_from_href(href)

        if hasattr(self, "add_note"):
            self.add_note(f"{id=}")
            self.add_note(f"{href=}")
        else:
            message += f"[{id=}, {href=}]"

        super().__init__(message, *args, **kwargs)


class BadStacObjectFilterError(ValueError):
    ...
