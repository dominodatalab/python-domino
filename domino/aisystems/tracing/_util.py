import os

def get_is_production() -> bool:
    return os.environ.get("DOMINO_AI_SYSTEM_IS_PROD", "false").lower() == "true"

