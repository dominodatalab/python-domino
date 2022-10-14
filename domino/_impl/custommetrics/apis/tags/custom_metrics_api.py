# coding: utf-8

"""
    Domino Public API

    Public API endpoints for Custom Metrics  # noqa: E501

    The version of the OpenAPI document: 5.3.0
    Generated by: https://openapi-generator.tech
"""

from domino._impl.custommetrics.paths.api_metric_values_v1.post import LogMetricValues
from domino._impl.custommetrics.paths.api_metric_values_v1_model_monitoring_id_metric.get import RetrieveMetricValues
from domino._impl.custommetrics.paths.api_metric_alerts_v1.post import SendMetricAlert


class CustomMetricsApi(
    LogMetricValues,
    RetrieveMetricValues,
    SendMetricAlert,
):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """
    pass
