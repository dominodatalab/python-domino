import os

from requests import models
from requests.auth import AuthBase, HTTPBasicAuth

from .constants import DOMINO_TOKEN_FILE_KEY_NAME, DOMINO_USER_API_KEY_KEY_NAME, \
    DOMINO_API_PROXY
from .http_request_manager import _SessionInitializer


class ProxyAuth(AuthBase, _SessionInitializer):
    """
    Class for authenticating requests using the Domino API Proxy.
    """

    def __init__(self, api_proxy):
        self.api_proxy = api_proxy

    def __call__(self, r):
        """
        Override the default __call__ method for the AuthBase base class.
        Note this override is no-op, the actual work happens in the initialize method.

        More more info, see:
        https://docs.python-requests.org/en/master/user/advanced/
        """
        return r

    def __initialize__(self, session):
        """
        Override the default __initialize__ method for the _SessionInitializer base class.
        """

        session.proxies.update({
            'http': f'http://{self.api_proxy}',
        })


class BearerAuth(AuthBase):
    """
    Class for authenticating requests by user supplied token.
    """

    def __init__(self, auth_token=None, domino_token_file=None):
        self.auth_token = auth_token
        self.domino_token_file = domino_token_file

    def _from_token_file(self):
        with open(self.domino_token_file, "r") as token_file:
            return token_file.readline().rstrip()

    def __call__(self, r):
        """
        Override the default __call__ method for the AuthBase base class

        More more info, see:
        https://docs.python-requests.org/en/master/user/advanced/
        """
        auth_token = (
            self._from_token_file() if self.domino_token_file else self.auth_token
        )
        r.headers["Authorization"] = "Bearer " + auth_token
        return r


def get_auth_by_type(api_key=None, auth_token=None, domino_token_file=None, api_proxy=None):
    """
    Return appropriate authentication object for requests.

    If no authentication credential is provided, the call fails with an AssertError

    Precedence in the case of multiple credentials is:
        1. api_proxy
        2. auth_token string
        3. domino_token_file
        4. api_key
        5. api_proxy_from_env
        6. domino_token_file_from_env
        7. api_key_from_env
    """

    if api_proxy:
        return ProxyAuth(api_proxy)
    elif auth_token:
        return BearerAuth(auth_token=auth_token)
    elif domino_token_file:
        return BearerAuth(domino_token_file=domino_token_file)
    elif api_key:
        return HTTPBasicAuth("", api_key)
    else:
        # In the case that no authentication type was passed when this method
        # called, fall back to deriving the auth info from the environment.
        api_proxy_from_env = os.getenv(DOMINO_API_PROXY)
        api_key_from_env = os.getenv(DOMINO_USER_API_KEY_KEY_NAME)
        domino_token_file_from_env = os.getenv(DOMINO_TOKEN_FILE_KEY_NAME)
        if api_key_from_env or domino_token_file_from_env or api_proxy_from_env:
            return get_auth_by_type(
                api_key=api_key_from_env, domino_token_file=domino_token_file_from_env, api_proxy=api_proxy_from_env
            )
        else:
            # All attempts failed -- nothing to do but raise an error.
            raise RuntimeError("Unable to authenticate: no authentication provided")
