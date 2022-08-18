import os

import pytest


@pytest.mark.skipif(os.getenv("DATA_SDK") != "yes", reason="Extra dependency required")
def test_data_sources_import():
    from domino.data_sources import ADLSConfig, DataSourceClient

    assert DataSourceClient
    assert ADLSConfig


@pytest.mark.skipif(os.getenv("DATA_SDK") != "yes", reason="Extra dependency required")
def test_data_sources_import_cant_find():  # noqa
    try:
        from domino.data_sources import NotADatasourceConfig

        assert NotADatasourceConfig
    except ImportError as exc:
        assert (
            "cannot import name 'NotADatasourceConfig' from 'domino.data_sources'"
            in str(exc)
        )
