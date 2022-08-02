import os

import pytest


@pytest.mark.skipif(os.getenv("DATA_SDK") != "yes", reason="Extra dependency required")
def test_data_sources_import():
    from domino.data_sources import ADLSConfig, DataSourceClient

    assert DataSourceClient
    assert ADLSConfig


@pytest.mark.skipif(os.getenv("DATA_SDK") != "yes", reason="Extra dependency required")
def test_data_sources_import_cant_find():
    try:
        from domino.data_sources import NotADatasourceConfig  # noqa
    except ImportError as exc:
        assert (
            "cannot import name 'NotADatasourceConfig' from 'domino.data_sources'"
            in str(exc)
        )


@pytest.mark.skipif(
    os.getenv("DATA_SDK") == "yes", reason="Testing failure when dependency is missing"
)
def test_data_sources_import_fails():
    try:
        from domino.data_sources import DataSourceClient  # noqa
    except ImportError as exc:
        assert "Please pip install dominodatalab-data" in str(exc)
    else:
        assert (
            False
        ), "Import should be failing when dominodatalab-data is not installed"
