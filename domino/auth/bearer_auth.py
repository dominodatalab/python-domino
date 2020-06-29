import requests


class BearerAuth(requests.auth.AuthBase):
    """
    This class is responsible for authenticating
    request using bearer token
    """
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
