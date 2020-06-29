import requests
import os


class BearerAuth(requests.auth.AuthBase):
    """
    This class is responsible for authenticating
    request using bearer token
    """
    def __init__(self, path_to_token_file):
        self.path_to_token_file = path_to_token_file
        self._assert_token_file_valid()

    def __call__(self, r):
        self._assert_token_file_valid()
        with open(self.path_to_token_file, 'r') as token_file:
            token = token_file.read()
        r.headers["authorization"] = "Bearer " + token
        return r

    def _assert_token_file_valid(self):
        if not os.path.isfile(self.path_to_token_file):
            raise Exception(f"Invalid token file path: {self.path_to_token_file}")
