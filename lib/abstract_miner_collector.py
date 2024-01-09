import abc
import requests
import time
import traceback

from collections import OrderedDict
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from typing import List, Dict

from metric_wrappers import WrMetric


class AbstractMinerCollector(abc.ABC):
    @abc.abstractmethod
    def collect(self) -> List[WrMetric]:
        return []

    def create_metrics(self, metric_class, metric_descs, labels) -> List[WrMetric]:
        return [WrMetric(
            metric_class=metric_class,
            name=name,
            labels=labels,
            **params,
        ) for name, params in metric_descs.items()]

    def create_miner_metrics(self,
                             miner_labels: OrderedDict[str, Dict],
                             counter_metrics_descs: Dict[str, Dict],
                             gauge_metrics_descs: Dict[str, Dict]) -> List[WrMetric]:
        label_keys = list(miner_labels.keys())
        metrics = self.create_metrics(CounterMetricFamily, counter_metrics_descs, label_keys)
        metrics.extend(self.create_metrics(GaugeMetricFamily, gauge_metrics_descs, label_keys))
        return metrics

    def create_gpu_metrics(self,
                           miner_labels: OrderedDict[str, Dict],
                           gpu_labels: OrderedDict[str, Dict],
                           counter_metrics_descs: Dict[str, Dict],
                           gauge_metrics_descs: Dict[str, Dict]) -> List[WrMetric]:
        label_keys = list(miner_labels.keys())
        label_keys.extend(gpu_labels.keys())
        metrics = self.create_metrics(CounterMetricFamily, counter_metrics_descs, label_keys)
        metrics.extend(self.create_metrics(GaugeMetricFamily, gauge_metrics_descs, label_keys))
        return metrics


class AbstractMinerJsonCollector(AbstractMinerCollector, abc.ABC):
    @abc.abstractmethod
    def json_collect(self, request_time: float, json_data):
        pass

    @property
    @abc.abstractmethod
    def api_url(self):
        pass

    def collect(self) -> List[WrMetric]:
        try:
            request_time = time.time()
            result = requests.get(self.api_url).json()
            return self.json_collect(request_time, result)
        except:
            # TODO better error handling
            traceback.print_exc()
            return []


class NoSupportedMinerCollector(AbstractMinerCollector):
    def collect(self) -> List[WrMetric]:
        return []
