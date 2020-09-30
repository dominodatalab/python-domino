from requests.auth import AuthBase
import logging
import requests


class _HttpRequestManager:
    """
    This class is responsible for
    making Http request calls
    """
    def __init__(self, auth: AuthBase):
        self.auth = auth
        self._logger = logging.getLogger(__name__)

    def post(self, url, data=None, json=None, **kwargs):
        return self._raise_for_status(requests.post(url, auth=self.auth, data=data, json=json, **kwargs))

    def get(self, url, **kwargs):
        return self._raise_for_status(requests.get(url, auth=self.auth, **kwargs))

    def put(self, url, data=None, **kwargs):
        return self._raise_for_status(requests.put(url, auth=self.auth, data=data, **kwargs))

    def delete(self, url, **kwargs):
        return self._raise_for_status(requests.delete(url, auth=self.auth, **kwargs))

    def get_raw(self, url):
        return self.get(url, stream=True).raw

    def _raise_for_status(self, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._logger.error(e.response.text)
            raise
        return response
