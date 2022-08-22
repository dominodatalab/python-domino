import os

import pytest


@pytest.mark.skipif(
    os.getenv("DATA_SDK") == "yes", reason="Testing failure when dependency is missing"
)
def test_data_sources_import_fails():  # noqa
    try:
        from domino.data_sources import DataSourceClient

        assert DataSourceClient
    except ImportError as exc:
        assert "Please pip install dominodatalab-data" in str(exc)
    else:
        assert (
            False
        ), "Import should be failing when dominodatalab-data is not installed"
