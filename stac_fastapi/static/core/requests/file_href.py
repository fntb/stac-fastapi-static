
from urllib.parse import urlparse
import pathlib


def file_path_to_file_uri(path: str):
    if not is_file_uri(path):
        raise ValueError(f"Not a path or 'file://' URI : {path}")

    path = urlparse(path).path

    return pathlib.Path(path).as_uri()


def file_uri_to_file_path(href: str):
    if not is_file_uri(href):
        raise ValueError(f"Not a path or 'file://' URI : {href}")

    return urlparse(href).path


def is_file_uri(href: str):
    return urlparse(href, scheme="file").scheme == "file"
