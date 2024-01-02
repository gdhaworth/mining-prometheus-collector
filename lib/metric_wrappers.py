import operator

from collections import OrderedDict
from collections.abc import Callable
from enum import Enum
from functools import reduce
from prometheus_client.core import Metric, GaugeMetricFamily, CounterMetricFamily
from typing import Dict, Sequence, Any, Optional


class LookupType(Enum):
    DIRECT = 1
    VALUE_PATH = 2
    CALLABLE = 3


class WrMetric:
    def __init__(self,
                 metric_class: type[GaugeMetricFamily] | type[CounterMetricFamily],
                 name: str,
                 labels: Sequence[str],
                 desc: str,
                 value_path: str,
                 transform: Callable[[Any], float | Optional[float]] = None
                 ):
        full_name = f'mining_{name}'
        self.value_path = value_path
        self.transform = transform
        self._metric = metric_class(name=full_name, documentation=desc, labels=labels)

    @staticmethod
    def value_at_path(base: Dict, path: str) -> Optional[Any]:
        value = base
        for key in path.split('.'):
            if key not in value.keys():
                return None
            value = value[key]
        return value

    @staticmethod
    def label_to_str(value):
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    @staticmethod
    def parse_label_values(base: Dict, label_descs: OrderedDict[str, Dict]) -> OrderedDict[str, str]:
        result = OrderedDict()
        for name, desc in label_descs.items():
            if desc['type'] == LookupType.DIRECT:
                result[name] = WrMetric.label_to_str(desc['value'])
            elif desc['type'] == LookupType.VALUE_PATH:
                result[name] = WrMetric.label_to_str(WrMetric.value_at_path(base, desc['path']))
            elif desc['type'] == LookupType.CALLABLE:
                result[name] = WrMetric.label_to_str(desc['func'](base))
            else:
                # this is a coding error, should not happen unless misconfigured
                raise f'Unknown label type: {desc["type"]}'
        return result

    def add_value(self, base: Dict, labels: Dict[str, str], timestamp: Optional[float] = None) -> None:
        value = self.value_at_path(base, self.value_path)
        if value is None:
            return
        if self.transform:
            value = self.transform(value)
        if value is None:
            return
        self._metric.add_metric(value=float(value), labels=list(labels.values()), timestamp=timestamp)

    @property
    def metric(self) -> Metric:
        return self._metric
