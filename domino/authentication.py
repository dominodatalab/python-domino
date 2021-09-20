from requests.auth import AuthBase, HTTPBasicAuth


class BearerAuth(AuthBase):
    """
    Class for authenticating requests by user supplied token.
    """

    def __init__(self, auth_token=None, domino_token_file=None):
        self.auth_token = auth_token
        self.domino_token_file = domino_token_file

    def _from_token_file(self):
        with open(self.domino_token_file, 'r') as token_file:
            return token_file.readline().rstrip()

    def __call__(self, r):
        """
        Override the default __call__ method for the AuthBase base class

        More more info, see:
        https://docs.python-requests.org/en/master/user/advanced/
        """
        auth_token = self._from_token_file() if self.domino_token_file else self.auth_token
        r.headers["Authorization"] = "Bearer " + auth_token
        return r


def get_auth_by_type(api_key=None, auth_token=None, domino_token_file=None):
    """
    Return appropriate authentication object for requests.

    If no authentication credential is provided, the call fails with an AssertError

    Precedence in the case of multiple credentials is:
        1. auth token string
        2. token file
        3. API key
    """

    assert any([api_key, auth_token, domino_token_file]), \
        "Unable to authenticate: no authentication method provided"

    if auth_token is not None:
        return BearerAuth(auth_token=auth_token)
    elif domino_token_file is not None:
        return BearerAuth(domino_token_file=domino_token_file)
    else:
        return HTTPBasicAuth('', api_key)
