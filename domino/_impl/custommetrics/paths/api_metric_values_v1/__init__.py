# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from domino._impl.custommetrics.paths.api_metric_values_v1 import Api

from domino._impl.custommetrics.paths import PathValues

path = PathValues.API_METRIC_VALUES_V1