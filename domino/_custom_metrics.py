from abc import ABC, abstractmethod
from copy import deepcopy
import json
from typing import Dict, List, Any, Optional, Union

from ._impl.custommetrics.model.metric_value_v1 import MetricValueV1
from ._impl.custommetrics.model.metric_alert_request_v1 import MetricAlertRequestV1
from ._impl.custommetrics.model.target_range_v1 import TargetRangeV1
from ._impl.custommetrics.paths.api_metric_alerts_v1.post import (
    request_body_metric_alert_request_v1,
)
from ._impl.custommetrics.model.new_metric_values_envelope_v1 import (
    NewMetricValuesEnvelopeV1,
)
from ._impl.custommetrics.model.new_metric_value_v1 import NewMetricValueV1
from ._impl.custommetrics.model.metric_tag_v1 import MetricTagV1
from ._impl.custommetrics.paths.api_metric_values_v1.post import (
    request_body_new_metric_values_envelope_v1,
)
from ._impl.custommetrics.paths.api_metric_values_v1_model_monitoring_id_metric.get import (
    _response_for_200,
    ApiResponseFor200,
)
from ._impl.custommetrics.model.metric_values_envelope_v1 import MetricValuesEnvelopeV1
from ._impl.custommetrics.model.metadata_v1 import MetadataV1
from ._impl.custommetrics.api_client import SerializedRequestBody
from ._impl.custommetrics import schemas
from ._impl.custommetrics import configuration


class _CustomMetricsClientBase(ABC):
    # Target range values
    LESS_THAN = "lessThan"
    LESS_THAN_EQUAL = "lessThanEqual"
    GREATER_THAN = "greaterThan"
    GREATER_THAN_EQUAL = "greaterThanEqual"
    BETWEEN = "between"

    @abstractmethod
    def trigger_alert(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        condition: str = None,
        lower_limit: Any = None,
        upper_limit: Any = None,
        description: str = None,
    ) -> None:
        pass

    @abstractmethod
    def log_metric(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        timestamp: str,
        tags: Dict = None,
    ) -> None:
        pass

    @abstractmethod
    def log_metrics(self, metric_values_array: List) -> None:
        pass

    @abstractmethod
    def read_metrics(
        self,
        model_monitoring_id: str,
        metric: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> Dict:
        pass


class _CustomMetricsClientGen(_CustomMetricsClientBase):
    """
    Client that partially re-uses the OpenAPI auto-generated code.
    """

    def __init__(self, parent, routes):
        self._parent = parent
        self._routes = routes

    def trigger_alert(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        condition: str = None,
        lower_limit: Any = None,
        upper_limit: Any = None,
        description: str = None,
    ) -> None:
        url = self._routes.metric_alerts()
        target_range: Optional[TargetRangeV1] = (
            None
            if condition is None
            else TargetRangeV1(
                condition=condition, lowerLimit=lower_limit, upperLimit=upper_limit
            )
        )
        req = MetricAlertRequestV1(
            modelMonitoringId=model_monitoring_id,
            metric=metric,
            value=value,
            targetRange=target_range, # type: ignore
            description=description,
        )
        ser_body: SerializedRequestBody = (
            request_body_metric_alert_request_v1.serialize(req, "application/json")
        )
        json_data = json.loads(
            ser_body["body"].decode("utf-8") # type: ignore
        )  # extra work to reuse request_manager
        self._parent.request_manager.post(url, json=json_data)

    def log_metric(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        timestamp: str,
        tags: Dict = None,
    ) -> None:
        item = {
            "modelMonitoringId": model_monitoring_id,
            "metric": metric,
            "value": value,
            "timestamp": timestamp,
        }
        if tags is not None:
            item["tags"] = tags
        self.log_metrics([item])

    def _to_new_metric_value(self, item: Dict) -> NewMetricValueV1:
        tags: Union[List[MetricTagV1],schemas.Unset] = schemas.unset
        if "tags" in item:
            tags = [MetricTagV1(key=k, value=v) for k, v in item["tags"].items()]
        ret = NewMetricValueV1(
            referenceTimestamp=item["timestamp"],
            metric=item["metric"],
            modelMonitoringId=item["modelMonitoringId"],
            value=item["value"],
            tags=tags,
        )
        return ret

    def log_metrics(self, metric_values_array: List) -> None:
        url = self._routes.log_metrics()
        newMetricValues = [self._to_new_metric_value(x) for x in metric_values_array]
        req = NewMetricValuesEnvelopeV1(newMetricValues=newMetricValues)
        ser_body: SerializedRequestBody = (
            request_body_new_metric_values_envelope_v1.serialize(
                req, "application/json"
            )
        )
        json_data = json.loads(
            ser_body["body"].decode("utf-8") # type: ignore
        )  # extra work to reuse request_manager
        self._parent.request_manager.post(url, json=json_data)

    def _from_metric_value(self, obj: MetricValueV1) -> Dict:
        # Numbers come in as Decimal objects but we want floats
        ret = {"timestamp": str(obj.referenceTimestamp), "value": float(obj["value"])}
        if obj.tags is not None:
            ret["tags"] = {tag["key"]: tag["value"] for tag in obj.tags}
        return ret

    def read_metrics(
        self,
        model_monitoring_id: str,
        metric: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> Dict:
        url = self._routes.read_metrics(model_monitoring_id, metric)
        params = {
            "startingReferenceTimestampInclusive": start_timestamp,
            "endingReferenceTimestampInclusive": end_timestamp,
        }
        res = self._parent.request_manager.get(url, params=params).json()
        mvs: MetricValuesEnvelopeV1 = MetricValuesEnvelopeV1.from_openapi_data_oapg(res)
        ret = {
            "metadata": dict(mvs.metadata),
            "metricValues": [self._from_metric_value(x) for x in mvs.metricValues],
        }
        return ret


class _CustomMetricsClient(_CustomMetricsClientBase):
    """
    Hand-rolled client kept in case of unexpected problems.
    """

    def __init__(self, parent, routes):
        self._parent = parent
        self._routes = routes

    def trigger_alert(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        condition: str = None,
        lower_limit: Any = None,
        upper_limit: Any = None,
        description: str = None,
    ) -> None:
        url = self._routes.metric_alerts()
        request = {
            "modelMonitoringId": model_monitoring_id,
            "metric": metric,
            "value": value,
            "targetRange": {"condition": condition},
        }
        if condition:
            request["targetRange"] = {"condition": condition}
            if lower_limit:
                request["targetRange"]["lowerLimit"] = lower_limit
            if upper_limit:
                request["targetRange"]["upperLimit"] = upper_limit
        if description:
            request["description"] = description
        self._parent.request_manager.post(url, json=request)

    def log_metric(
        self,
        model_monitoring_id: str,
        metric: str,
        value: Any,
        timestamp: str,
        tags: Dict = None,
    ) -> None:
        item = {
            "modelMonitoringId": model_monitoring_id,
            "metric": metric,
            "value": value,
            "timestamp": timestamp,
        }
        if tags is not None:
            item["tags"] = tags
        self.log_metrics([item])

    def _rewrite_tags_in(self, item) -> List:
        return [{"key": k, "value": v} for k, v in item["tags"].items()]

    def _rewrite_tags_out(self, item) -> Dict:
        return {v["key"]: v["value"] for v in item["tags"]}

    def log_metrics(self, metric_values_array: List) -> None:
        url = self._routes.log_metrics()
        new_values = []
        for item in metric_values_array:
            new_item = deepcopy(item)
            if "tags" in new_item:
                new_item["tags"] = self._rewrite_tags_in(new_item)
            if "timestamp" in new_item:
                new_item["referenceTimestamp"] = new_item["timestamp"]
                del new_item["timestamp"]
            new_values.append(new_item)

        request = {"newMetricValues": new_values}
        self._parent.request_manager.post(url, json=request)

    def read_metrics(
        self,
        model_monitoring_id: str,
        metric: str,
        start_timestamp: str,
        end_timestamp: str,
    ) -> Dict:
        url = self._routes.read_metrics(model_monitoring_id, metric)
        params = {
            "startingReferenceTimestampInclusive": start_timestamp,
            "endingReferenceTimestampInclusive": end_timestamp,
        }
        res = self._parent.request_manager.get(url, params=params).json()
        if "metricValues" in res:
            for item in res["metricValues"]:
                if "referenceTimestamp" in item:
                    item["timestamp"] = item["referenceTimestamp"]
                    del item["referenceTimestamp"]
                if "tags" in item:
                    item["tags"] = self._rewrite_tags_out(item)
        return res
