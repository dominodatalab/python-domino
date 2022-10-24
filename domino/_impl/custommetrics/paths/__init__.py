# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from domino._impl.custommetrics.apis.path_to_api import path_to_api

import enum


class PathValues(str, enum.Enum):
    API_METRIC_ALERTS_V1 = "/api/metricAlerts/v1"
    API_METRIC_VALUES_V1 = "/api/metricValues/v1"
    API_METRIC_VALUES_V1_MODEL_MONITORING_ID_METRIC = "/api/metricValues/v1/{modelMonitoringId}/{metric}"
