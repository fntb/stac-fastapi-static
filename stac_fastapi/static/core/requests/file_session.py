
import requests
from requests_file import FileAdapter


class FileSession(requests.Session):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mount("file://", FileAdapter())
