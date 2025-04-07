import urllib.parse


def guess_id_from_href(href: str) -> str | None:
    path = urllib.parse.urlparse(href).path
    path_parts = path.split("/")

    if len(path_parts) >= 2:

        candidate_file_name = path_parts[-1]
        candidate_dir_name = path_parts[-2]

        if candidate_file_name == candidate_dir_name + ".json":
            return candidate_dir_name

    return None
