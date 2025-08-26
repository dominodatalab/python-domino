from unittest.mock import patch
import os
import pytest

from domino.aisystems._constants import MIN_MLFLOW_VERSION, MIN_DOMINO_VERSION
from domino.aisystems._verify_domino_support import _get_version_endpoint
from domino.exceptions import UnsupportedOperationException
from ..conftest import TEST_AI_SYSTEMS_ENV_VARS

def test_get_version_endpoint():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_API_HOST": "http://localhost:1111/"}, clear=True):
                assert _get_version_endpoint() == "http://localhost:1111/version"

def test_verify_domino_support_domino_and_mlflow_correct_version(verify_domino_support_fixture):
        from domino.aisystems._verify_domino_support import _verify_domino_support_impl
        verify_domino_support_fixture['mock_get_domino_version'].return_value = MIN_DOMINO_VERSION
        verify_domino_support_fixture['mock_get_mlflow_version'].return_value = MIN_MLFLOW_VERSION

        # Should not raise
        _verify_domino_support_impl()

def test_verify_domino_support_should_be_idempotent(verify_domino_support_fixture, mocker):
        from domino.aisystems._verify_domino_support import verify_domino_support
        verify_domino_support_fixture['mock_get_domino_version'].return_value = MIN_DOMINO_VERSION
        verify_domino_support_fixture['mock_get_mlflow_version'].return_value = MIN_MLFLOW_VERSION

        import domino.aisystems._verify_domino_support
        get_domino_version_spy = mocker.spy(domino.aisystems._verify_domino_support, "_get_domino_version")

        verify_domino_support()
        verify_domino_support()

        assert get_domino_version_spy.call_count == 1

def test_verify_domino_support_domino_wrong_version(verify_domino_support_fixture):
        from domino.aisystems._verify_domino_support import _verify_domino_support_impl
        verify_domino_support_fixture['mock_get_domino_version'].return_value = "6.1.2"

        with pytest.raises(UnsupportedOperationException) as exn:
                _verify_domino_support_impl()

        assert str(exn.value) == "This version of Domino doesn’t support the aisystems package."

def test_verify_domino_support_mlflow_wrong_version(verify_domino_support_fixture):
        from domino.aisystems._verify_domino_support import _verify_domino_support_impl
        verify_domino_support_fixture['mock_get_domino_version'].return_value = MIN_DOMINO_VERSION
        verify_domino_support_fixture['mock_get_mlflow_version'].return_value = '3.1.0'

        with pytest.raises(UnsupportedOperationException) as exn:
                _verify_domino_support_impl()

        assert str(exn.value) == f"This code requires you to install mlflow>={MIN_MLFLOW_VERSION}"

@pytest.fixture
def verify_domino_support_fixture():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_API_HOST": "http://localhost:1111/"}, clear=True), \
                patch('domino.aisystems._verify_domino_support._get_domino_version') as mock_get_domino_version, \
                patch('domino.aisystems._verify_domino_support._get_mlflow_version') as mock_get_mlflow_version:
                yield { 'mock_get_domino_version': mock_get_domino_version, 'mock_get_mlflow_version': mock_get_mlflow_version }
