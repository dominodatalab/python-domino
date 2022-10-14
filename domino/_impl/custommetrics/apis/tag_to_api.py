import typing_extensions

from domino._impl.custommetrics.apis.tags import TagValues
from domino._impl.custommetrics.apis.tags.custom_metrics_api import CustomMetricsApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.CUSTOM_METRICS: CustomMetricsApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.CUSTOM_METRICS: CustomMetricsApi,
    }
)
