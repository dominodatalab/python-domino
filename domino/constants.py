"""
Minimum Domino version supported by this python-domino library
"""
MINIMUM_SUPPORTED_DOMINO_VERSION = "4.1.0"

"""
Minimum Domino version supporting on demand spark cluster
"""
MINIMUM_ON_DEMAND_SPARK_CLUSTER_SUPPORT_DOMINO_VERSION = "4.2.0"

"""
Minimum Domino version supporting distributed compute cluster launching
"""
MINIMUM_DISTRIBUTED_CLUSTER_SUPPORT_DOMINO_VERSION = "4.5.0"

"""
Distributed compute cluster types and their minimum supported Domino version
"""
CLUSTER_TYPE_MIN_SUPPORT = [("Spark", "4.5.0"), ("Ray", "4.5.0"), ("Dask", "4.6.0")]

"""
Minimum Domino version that supports compute cluster autoscaling
"""
COMPUTE_CLUSTER_AUTOSCALING_MIN_SUPPORT_DOMINO_VERSION = "5.0.0"

"""
Minimum Domino version supporting external volume mounts
"""
MINIMUM_EXTERNAL_VOLUME_MOUNTS_SUPPORT_DOMINO_VERSION = "4.3.3"

"""
Environment variable names used by this python-domino library. The values
here match the environment variable names a user would find on a deploymemt.
"""
DOMINO_TOKEN_FILE_KEY_NAME = "DOMINO_TOKEN_FILE"
DOMINO_USER_API_KEY_KEY_NAME = "DOMINO_USER_API_KEY"
DOMINO_HOST_KEY_NAME = "DOMINO_API_HOST"
DOMINO_LOG_LEVEL_KEY_NAME = "DOMINO_LOG_LEVEL"
DOMINO_USER_NAME_KEY_NAME = "DOMINO_USER_NAME"
