import os
import pytest
import time

from domino import Domino
from domino.http_request_manager import _HttpRequestManager

os.environ["DOMINO_MAX_RETRIES"] = "3"


def test_versioning(requests_mock, dummy_hostname):
    """validates domino version checking is correct"""

    # Mock a typical response from the jobs status API endpoint (GET)
    requests_mock.get(f"{dummy_hostname}/version", json={"version": "5.10.0"})

    dom = Domino(host=dummy_hostname, project="rand_user/rand_project", api_key="rand_api_key")

    dep_version = dom.deployment_version().get("version")
    assert dep_version == "5.10.0"
    assert dom.requires_at_least("5.3.0")
    with pytest.raises(Exception):
        dom.requires_at_least("5.11.0")

def test_request_session(test_auth_base):
     request_manager = _HttpRequestManager(auth=test_auth_base)
     start_time = time.time()
     try:
         response = request_manager.request_session.get(
             'https://localhost:9999' # ConnectionError
         )
     except Exception as ex:
         print('It failed :(', ex.__class__.__name__)
     else:
         print('It eventually worked', response.status_code)
     finally:
         end_time = time.time()
         total_time = end_time - start_time
         assert(total_time > 5) # actual value should be around 6.0210....
