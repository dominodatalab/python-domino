"""
Minimum Domino version supported by this python-domino library
"""
MINIMUM_SUPPORTED_DOMINO_VERSION = '4.1.0'

"""
Minimum Domino version supporting on demand spark cluster
"""
MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION = '4.2.0'

"""
Minimum Domino version supporting distributed compute cluster launching
"""
MINIMUM_DISTRIBUTED_CLUSTER_SUPPORT_DOMINO_VERSION = '4.5.0'

"""
Distributed compute cluster types and their minimum supported Domino version
"""
CLUSTER_TYPE_MIN_SUPPORT = [("Spark", "4.5.0"), ("Ray", "4.5.0")]

"""
Environment variable names used by this python-domino library
"""
DOMINO_TOKEN_FILE_KEY_NAME = 'DOMINO_TOKEN_FILE'
DOMINO_USER_API_KEY_KEY_NAME = 'DOMINO_USER_API_KEY'
DOMINO_HOST_KEY_NAME = 'DOMINO_API_HOST'
DOMINO_LOG_LEVEL_KEY_NAME = 'DOMINO_LOG_LEVEL'
