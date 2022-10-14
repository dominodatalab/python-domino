# coding: utf-8

"""
    Domino Public API

    Public API endpoints for Custom Metrics  # noqa: E501

    The version of the OpenAPI document: 5.3.0
    Generated by: https://openapi-generator.tech
"""

from datetime import date, datetime  # noqa: F401
import decimal  # noqa: F401
import functools  # noqa: F401
import io  # noqa: F401
import re  # noqa: F401
import typing  # noqa: F401
import typing_extensions  # noqa: F401
import uuid  # noqa: F401

import frozendict  # noqa: F401

from domino._impl.custommetrics import schemas  # noqa: F401


class MetricValuesEnvelopeV1(
    schemas.DictSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        required = {
            "metadata",
            "metricValues",
        }
        
        class properties:
            
            
            class metricValues(
                schemas.ListSchema
            ):
            
            
                class MetaOapg:
                    
                    @staticmethod
                    def items() -> typing.Type['MetricValueV1']:
                        return MetricValueV1
            
                def __new__(
                    cls,
                    arg: typing.Union[typing.Tuple['MetricValueV1'], typing.List['MetricValueV1']],
                    _configuration: typing.Optional[schemas.Configuration] = None,
                ) -> 'metricValues':
                    return super().__new__(
                        cls,
                        arg,
                        _configuration=_configuration,
                    )
            
                def __getitem__(self, i: int) -> 'MetricValueV1':
                    return super().__getitem__(i)
        
            @staticmethod
            def metadata() -> typing.Type['MetadataV1']:
                return MetadataV1
            __annotations__ = {
                "metricValues": metricValues,
                "metadata": metadata,
            }
    
    metadata: 'MetadataV1'
    metricValues: MetaOapg.properties.metricValues
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["metricValues"]) -> MetaOapg.properties.metricValues: ...
    
    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["metadata"]) -> 'MetadataV1': ...
    
    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...
    
    def __getitem__(self, name: typing.Union[typing_extensions.Literal["metricValues", "metadata", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)
    
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["metricValues"]) -> MetaOapg.properties.metricValues: ...
    
    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["metadata"]) -> 'MetadataV1': ...
    
    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...
    
    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["metricValues", "metadata", ], str]):
        return super().get_item_oapg(name)
    

    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, ],
        metadata: 'MetadataV1',
        metricValues: typing.Union[MetaOapg.properties.metricValues, list, tuple, ],
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'MetricValuesEnvelopeV1':
        return super().__new__(
            cls,
            *args,
            metadata=metadata,
            metricValues=metricValues,
            _configuration=_configuration,
            **kwargs,
        )

from .metadata_v1 import MetadataV1
from .metric_value_v1 import MetricValueV1
