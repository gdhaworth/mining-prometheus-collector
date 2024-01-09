import dictlib

from collections import OrderedDict
from collections.abc import Callable
from prometheus_client.core import Metric, GaugeMetricFamily, CounterMetricFamily
from typing import Dict, Sequence, Any, Optional


class WrMetric:
    def __init__(self,
                 metric_class: type[GaugeMetricFamily] | type[CounterMetricFamily],
                 name: str,
                 labels: Sequence[str],
                 desc: str,
                 value_path: str,
                 transform: Callable[[Any, ...], float | Optional[float]] = None
                 ):
        full_name = f'mining_{name}'
        self.value_path = value_path
        self.transform = transform
        self._labels = list(labels)
        self._metric = metric_class(name=full_name, documentation=desc, labels=self._labels)

    @staticmethod
    def value_at_path(base: Dict, path: str, i: int) -> Optional[Any]:
        if path == '.':
            return base
        if i is not None:
            path = path.replace('[i]', f'[{i}]')
        return dictlib.dig(base, path)

    @staticmethod
    def label_as_str(value) -> str:
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    @staticmethod
    def lookup_str_value(base: Dict, desc: Dict, i: int) -> Optional[str]:
        if 'value' in desc.keys():
            int_result = desc['value']
        elif 'path' in desc.keys():
            int_result = WrMetric.value_at_path(base, desc['path'], i)
        else:
            int_result = base

        if 'join' in desc.keys():
            int_result = ' '.join([WrMetric.value_at_path(int_result, path, i) for path in desc['join']])

        if 'transform' in desc.keys():
            int_result = desc['transform'](int_result)

        if 'coalesce' in desc.keys():
            for desc_coalesced in desc['coalesce']:
                c_result = WrMetric.lookup_str_value(int_result, desc_coalesced, i)
                if c_result is not None and (not isinstance(c_result, str) or len(c_result) > 0):
                    return c_result
            return None

        return int_result

    @staticmethod
    def parse_label_values(base: Dict, label_descs: OrderedDict[str, Dict], i: int = None) -> OrderedDict[str, str]:
        result = OrderedDict()
        for name, desc in label_descs.items():
            result[name] = WrMetric.label_as_str(WrMetric.lookup_str_value(base, desc, i))
        return result

    def add_value(self, base: Dict, labels: Dict[str, str], timestamp: Optional[float] = None, i: int = None) -> None:
        value = self.value_at_path(base, self.value_path, i)
        if value is None:
            return
        if self.transform:
            value = self.transform(value, i)
        if value is None:
            return
        # TODO make the raise optional at runtime, but this is likely a programming error, not something unexpected from
        # the api
        if list(labels.keys()) != self._labels:
            print(self._labels)
            print(list(labels.keys()))
            raise 'Labels do not match'

        # Make sure they're in order... yes paranoid but no unit tests yet
        label_values = [labels[label] for label in self._labels]

        self._metric.add_metric(value=float(value), labels=label_values, timestamp=timestamp)

    @property
    def metric(self) -> Metric:
        return self._metric
