# this file is for documenting environment variables and has no functional value

"""
:DOMINO_AI_SYSTEM_CONFIG_PATH: For configuring the location of the ai_system_config.yaml file.
    If not set, defaults to './ai_system_config.yaml'.
:type: str

:DOMINO_AI_SYSTEM_IS_PROD: Indicates if the AI System is running in production mode.
    Set to 'true' to optimize for production.
:type: str

:DOMINO_APP_ID: Indicates the ID of the AI System application. Must be set in production mode.
:type: str

:MLFLOW_TRACKING_URI: Used to configure Mlflow functionality. It is required in order for library to work and will
    be set automatically when running in Domino.
:type: str
"""
