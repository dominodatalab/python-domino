from unittest.mock import patch
import os

from domino.aisystems import read_ai_system_config
from domino.aisystems.read_ai_system_config import flatten_dict
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
