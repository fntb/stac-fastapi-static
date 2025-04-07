from typing import (
    Literal,
    Union
)

from pydantic import (
    field_validator,
    PositiveInt,
    HttpUrl,
    FileUrl,
    Field
)

from pydantic_settings import SettingsConfigDict

from stac_fastapi.types.config import ApiSettings


class Settings(ApiSettings):
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/

    environment: Literal["dev", "prod"] = Field(
        "prod",
        description="In dev mode python errors returned from the API are not sanitized and may expose secrets."
    )

    catalog_href: Union[HttpUrl, FileUrl] = Field(
        description=(
            "Url of the static STAC catalog to expose."
            " `file://` and `http(s)://` schemes are supported for locally or remotely hosted catalogs."
        )
    )

    @field_validator("catalog_href", mode="after")
    def catalog_href_to_str(cls, value):
        return str(value)

    landing_page_child_collections_max_depth: PositiveInt = Field(
        2,
        description=""
    )

    assume_best_practice_layout: bool = Field(
        False,
        description=(
            "Asserts that the underlying static catalog `catalog_href` implements the best practices layout"
            " (as described here https://github.com/radiantearth/stac-spec/blob/v1.1.0/best-practices.md"
            " or here https://pystac.readthedocs.io/en/latest/api/layout.html#pystac.layout.BestPracticesLayoutStrategy)"
            ", specifically that item hrefs end with `<id>/<id>.json`."
            " This assumption enables significant optimization and performance enhancement."
        )
    )
    assume_extent_spec: bool = Field(
        True,
        description=(
            "Asserts that the underlying static catalog `catalog_href` correctly implements the Extent spec"
            " (as described here https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#extents)"
            ", specifically that the first bbox / interval is an aggregate of the others."
            " Any fully STAC-compliant catalog must implement this spec correctly"
            " so this option can be considered safe to enable even without familiarity with the underlying catalog."
            " This assumption enables finer extent-based filtering."
        )
    )
    assume_absolute_hrefs: bool = Field(
        False,
        description=(
            "Asserts that the underlying catalog hrefs (in links and assets) are always absolute urls or paths (instead of relative ones)."
            " This assumption enables a minor (linear) optimization and performance enhancement."
        )
    )

    cache: bool = Field(
        True,
        description=(
            "Enables caching the underlying static catalog."
            " Caching directives (headers) are respected so this option can be considered safe"
            " (if the remote catalog has properly configured cache directives)."
            " Caching is done on disk in a temporary directory."
            " This option is ignored when the underlying catalog is locally hosted (`file://`)."
            " This assumption enables significant performance enhancement."
        )
    )

    cors_origins: str = "*"
    cors_methods: str = "GET,POST,OPTIONS"

    log_level: str = "WARNING"

    @field_validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("cors_methods")
    def parse_cors_methods(cls, v):
        """Parse CORS methods."""
        return [method.strip() for method in v.split(",")]

    model_config = SettingsConfigDict(
        **{**ApiSettings.model_config, **{"env_nested_delimiter": "__"}}
    )
