import logging
import os
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from requests.auth import AuthBase

from ._version import __version__
from .constants import DOMINO_VERIFY_CERTIFICATE
from .exceptions import ReloginRequiredException


R_SESSION_MAX_RETRIES = 4

class _SessionInitializer:
    def __initialize__(self, session):
        raise NotImplementedError('Session initializers must be callable.')

class _HttpRequestManager:
    """
    This class is responsible for
    making Http request calls
    """

    def __init__(self, auth: AuthBase):
        self.auth = auth
        self._logger = logging.getLogger(__name__)
        self.request_session = self._set_session()

        if isinstance(self.auth, _SessionInitializer):
            self.auth.__initialize__(self._set_session())

    def _set_session(self):
        """
        Initialize a request session with retry to help manage connections drop.
        """
        self.session = requests.Session()
        retries = Retry(
            total=int(os.getenv("DOMINO_MAX_RETRIES", str(R_SESSION_MAX_RETRIES))),
            backoff_factor=1,  # retry seconds
            status_forcelist=[408, 502, 503, 504],
        )

        if os.environ.get(DOMINO_VERIFY_CERTIFICATE, None) in ["false", "f", "n", "no"]:
            warning = "InsecureRequestWarning: Bypassing certificate verification is strongly ill-advised"
            logging.warning(warning)
            print(warning)
            self.session.verify = False

        retry_adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", retry_adapter)
        return self.session

    def post(self, url, data=None, json=None, **kwargs):
        return self._raise_for_status(
            self.request_session.post(
                url, auth=self.auth, data=data, json=json, **kwargs
            )
        )

    def patch(self, url, data=None, json=None, **kwargs):
        return self._raise_for_status(
            self.request_session.patch(
                url, auth=self.auth, data=data, json=json, **kwargs
            )
        )

    def get(self, url, **kwargs):
        return self._raise_for_status(
            self.request_session.get(url, auth=self.auth, **kwargs)
        )

    def put(self, url, data=None, **kwargs):
        return self._raise_for_status(
            self.request_session.put(url, auth=self.auth, data=data, **kwargs)
        )

    def delete(self, url, **kwargs):
        return self._raise_for_status(
            self.request_session.delete(url, auth=self.auth, **kwargs)
        )

    def get_raw(self, url):
        return self.get(url, stream=True).raw

    def _raise_for_status(self, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTPStatus.CONFLICT:
                raise ReloginRequiredException("Temporary credentials expired")
            # Sometimes, the error response is a long HTML page.
            # We don't want to log error the whole response html in those cases.
            if not bool(BeautifulSoup(e.response.text, "html.parser").find()):
                self._logger.error(e.response.text)
            else:
                self._logger.debug(e.response.text)
            raise
        return response
