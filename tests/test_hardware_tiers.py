import uuid
from pprint import pformat

import pytest

from domino import Domino
from domino.helpers import domino_is_reachable
from domino.exceptions import ProjectNotFoundException


@pytest.mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
def test_hardware_tier_create(default_domino_client):
    """
    Confirm that the python-domino client can create a new hardware tier
    """
    new_hardware_tier_id = f"hardware-tier-name-{str(uuid.uuid4())}"
    new_hardware_tier_name = f"hardware-tier-name-{str(uuid.uuid4())}"
    node_pool = f"node-pool-{str(uuid.uuid4())}"
    response = default_domino_client.hardware_tier_create(new_hardware_tier_id, new_hardware_tier_name, node_pool)
    assert response.status_code == 200, f"{response.status_code}: {response.reason}"

    default_domino_client.hardware_tier_archive(new_hardware_tier_id)

@pytest.mark.skipif(not domino_is_reachable(), reason="No access to a live Domino deployment")
def test_archiving_non_existent_hardware_tier_raises_appropriate_error(default_domino_client):
    new_hardware_tier_id = f"hardware-tier-name-{str(uuid.uuid4())}"
    default_domino_client.hardware_tier_archive(new_hardware_tier_id)
