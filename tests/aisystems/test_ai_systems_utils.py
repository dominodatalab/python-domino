from unittest.mock import patch
import os
import pytest

from domino.aisystems import read_ai_system_config
from domino.aisystems._util import _get_version_endpoint, flatten_dict,  build_eval_result_tag
from domino.exceptions import UnsupportedOperationException
from ..conftest import TEST_AI_SYSTEMS_ENV_VARS

def test_read_ai_system_config_path_from_env_var():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS, clear=True):
                config_values = read_ai_system_config()

                assert config_values['version'] == 1.0
                assert config_values['chat_assistant']['model'] == 'gpt-3.5-turbo'
                assert config_values['chat_assistant']['temperature'] == 0.7
                assert config_values['chat_assistant']['max_tokens'] == 1500

def test_read_ai_system_config_path_from_override_arg():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_AI_SYSTEM_CONFIG_PATH": "broken_path"}, clear=True):
                config_values = read_ai_system_config("tests/assets/ai_system_config.yaml")

                assert config_values['version'] == 1.0
                assert config_values['chat_assistant']['model'] == 'gpt-3.5-turbo'
                assert config_values['chat_assistant']['temperature'] == 0.7
                assert config_values['chat_assistant']['max_tokens'] == 1500

def test_get_version_endpoint():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_API_HOST": "http://localhost:1111/"}, clear=True):
                assert _get_version_endpoint() == "http://localhost:1111/version"

def test_flatten_dict():
        nested_dict = {
                'a': 1,
                'b': {
                        'c': 2,
                        'd': { 'e': 3 }
                },
                'f': 4
        }
        flat_dict = flatten_dict(nested_dict)
        expected_flat_dict = {
                'a': 1,
                'b.c': 2,
                'b.d.e': 3,
                'f': 4
        }
        assert flat_dict == expected_flat_dict

def test_build_eval_result_tags():
        assert build_eval_result_tag('my_metric', '1') ==  'domino.prog.metric.my_metric', 'numbers should be metrics'
        assert build_eval_result_tag('my_label', 'cat') ==  'domino.prog.label.my_label', 'strings should be labels'

def test_verify_domino_support_domino_correct_version():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_API_HOST": "http://localhost:1111/"}, clear=True):
                with patch('domino.aisystems._util._get_domino_version') as mock_get_domino_version:
                        from domino.aisystems._util import verify_domino_support
                        mock_get_domino_version.return_value = "6.2.1"

                        # Should not raise
                        verify_domino_support()

def test_verify_domino_support_domino_wrong_version():
        with patch.dict(os.environ, TEST_AI_SYSTEMS_ENV_VARS | {"DOMINO_API_HOST": "http://localhost:1111/"}, clear=True):
                with patch('domino.aisystems._util._get_domino_version') as mock_get_domino_version:
                        from domino.aisystems._util import verify_domino_support
                        mock_get_domino_version.return_value = "6.1.2"

                        with pytest.raises(UnsupportedOperationException) as exn:
                                verify_domino_support()

                        assert str(exn.value) == "This version of Domino doesn’t support the aisystems package."
