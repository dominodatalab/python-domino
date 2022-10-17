import typing_extensions

from domino._impl.custommetrics.paths import PathValues
from domino._impl.custommetrics.apis.paths.api_metric_alerts_v1 import ApiMetricAlertsV1
from domino._impl.custommetrics.apis.paths.api_metric_values_v1 import ApiMetricValuesV1
from domino._impl.custommetrics.apis.paths.api_metric_values_v1_model_monitoring_id_metric import ApiMetricValuesV1ModelMonitoringIdMetric

PathToApi = typing_extensions.TypedDict(
    'PathToApi',
    {
        PathValues.API_METRIC_ALERTS_V1: ApiMetricAlertsV1,
        PathValues.API_METRIC_VALUES_V1: ApiMetricValuesV1,
        PathValues.API_METRIC_VALUES_V1_MODEL_MONITORING_ID_METRIC: ApiMetricValuesV1ModelMonitoringIdMetric,
    }
)

path_to_api = PathToApi(
    {
        PathValues.API_METRIC_ALERTS_V1: ApiMetricAlertsV1,
        PathValues.API_METRIC_VALUES_V1: ApiMetricValuesV1,
        PathValues.API_METRIC_VALUES_V1_MODEL_MONITORING_ID_METRIC: ApiMetricValuesV1ModelMonitoringIdMetric,
    }
)
