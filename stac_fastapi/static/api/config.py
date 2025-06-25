from typing import (
    Literal,
    Union,
    List
)

from pydantic import (
    field_validator,
    PositiveInt,
    Field
)

from pydantic_settings import SettingsConfigDict

from stac_fastapi.types.config import ApiSettings

from stac_fastapi.static.core.requests import (
    is_file_uri,
    file_path_to_file_uri
)


class Settings(ApiSettings):
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/

    # --- Inherited from ApiSettings, repeated for documentation ---

    stac_fastapi_title: str = "stac-fastapi"
    stac_fastapi_description: str = "stac-fastapi"
    stac_fastapi_version: str = "0.1"
    stac_fastapi_landing_id: str = "stac-fastapi"

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    reload: bool = True

    # Enable Pydantic validation for output Response
    enable_response_models: bool = False

    # Enable direct `Response` from endpoint, skipping validation and serialization
    enable_direct_response: bool = False

    openapi_url: str = "/api"
    docs_url: str = "/api.html"
    root_path: str = ""

    # --- Custom Settings ---

    environment: Literal["dev", "development", "prod", "production"] = Field(
        "production",
        description="In dev mode python errors returned from the API are not sanitized and may expose secrets.",
        deprecated="Previous dev mode is assumed if and only if log_level is set to debug"
    )

    catalog_href: Union[str] = Field(
        description=(
            "Url of the static STAC catalog to expose."
            " `file://` and `http(s)://` schemes are supported for locally or remotely hosted catalogs."
        )
    )

    @field_validator("catalog_href", mode="after")
    def catalog_href_to_str(cls, value):
        if is_file_uri(value):
            return file_path_to_file_uri(value)
        else:
            return value

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
        ),
        deprecated=True
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

    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "OPTIONS"]

    log_level: str = "warning"

    model_config = SettingsConfigDict(
        **{**ApiSettings.model_config, **{"env_nested_delimiter": "__"}}
    )
