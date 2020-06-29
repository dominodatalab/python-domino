from requests.auth import AuthBase
import requests


class _HttpRequestManager:
    """
    This class is responsible for
    making Http request calls
    """
    def __init__(self, auth: AuthBase):
        self.auth = auth

    def set_auth(self, auth: AuthBase):
        self.auth = auth

    def post(self, url, data=None, json=None, **kwargs):
        return requests.post(url, auth=self.auth, data=data, json=json, **kwargs)

    def get(self, url, **kwargs):
        return requests.get(url, auth=self.auth, **kwargs)

    def put(self, url, data=None, **kwargs):
        return requests.put(url, auth=self.auth, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return requests.delete(url, auth=self.auth, **kwargs)