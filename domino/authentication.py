import os

from requests.auth import AuthBase, HTTPBasicAuth

from .constants import DOMINO_TOKEN_FILE_KEY_NAME, DOMINO_USER_API_KEY_KEY_NAME


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


def get_auth_by_type(api_key=None, auth_token=None, domino_token_file=None):
    """
    Return appropriate authentication object for requests.

    If no authentication credential is provided, the call fails with an AssertError

    Precedence in the case of multiple credentials is:
        1. auth_token string
        2. domino_token_file
        3. api_key
        4. domino_token_file_from_env
        5. api_key_from_env
    """

    if auth_token is not None:
        return BearerAuth(auth_token=auth_token)
    elif domino_token_file is not None:
        return BearerAuth(domino_token_file=domino_token_file)
    elif api_key is not None:
        return HTTPBasicAuth("", api_key)
    else:
        # In the case that no authentication type was passed when this method
        # called, fall back to deriving the auth info from the environment.
        api_key_from_env = os.getenv(DOMINO_USER_API_KEY_KEY_NAME)
        domino_token_file_from_env = os.getenv(DOMINO_TOKEN_FILE_KEY_NAME)
        if api_key_from_env or domino_token_file_from_env:
            return get_auth_by_type(
                api_key=api_key_from_env, domino_token_file=domino_token_file_from_env
            )
        else:
            # All attempts failed -- nothing to do but raise an error.
            raise RuntimeError("Unable to authenticate: no authentication provided")
