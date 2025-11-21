# this file is for documenting environment variables and has no functional value

"""
:DOMINO_AGENT_CONFIG_PATH: For configuring the location of the agent_config.yaml file.
    If not set, defaults to './agent_config.yaml'.
:type: str

:DOMINO_AGENT_IS_PROD: Indicates if the Agent is running in production mode.
    Set to 'true' to optimize for production.
:type: str

:DOMINO_APP_ID: Indicates the ID of the Agent application. Must be set in production mode.
:type: str

:MLFLOW_TRACKING_URI: Used to configure Mlflow functionality. It is required in order for library to work and will
    be set automatically when running in Domino.
:type: str
"""
