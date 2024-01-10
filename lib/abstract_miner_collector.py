import abc
import requests
import time
import traceback

from functools import partial
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from typing import List, Dict, Callable

import transformers

from metric_wrappers import WrMetric


class AbstractMinerCollector(abc.ABC):
    @abc.abstractmethod
    def collect(self) -> List[WrMetric]:
        return []

    def _create_metrics(self, metric_class, metric_descs, labels) -> List[WrMetric]:
        return [WrMetric(
            metric_class=metric_class,
            name=name,
            labels=labels,
            **params,
        ) for name, params in metric_descs.items()]

    def create_counter_gauge_metrics(self,
                                     counter_metrics_descs: Dict[str, Dict],
                                     gauge_metrics_descs: Dict[str, Dict],
                                     labels: List[str]) -> List[WrMetric]:
        metrics = self._create_metrics(CounterMetricFamily, counter_metrics_descs, labels)
        metrics.extend(self._create_metrics(GaugeMetricFamily, gauge_metrics_descs, labels))
        return metrics


class AbstractMinerJsonCollector(AbstractMinerCollector, abc.ABC):
    def __init__(self, config: Dict):
        if config:
            gpus = config['gpus'].get(transformers.hostname(), {})
            self._pci_to_gpu = {gpu['pci_id']: gpu for gpu in gpus}

            addl_labels = set()
            for _, gpu in self._pci_to_gpu.items():
                gpu_addl_labels = gpu.get('addl_labels', {})
                addl_labels.update(gpu_addl_labels.keys())
            self._addl_labels = list(addl_labels)
        else:
            self._pci_to_gpu = None
            self._addl_labels = []

    def addl_gpu_labels_from_config(self, pci_id_func: Callable, value_path: str = None) -> Dict:
        if not self._pci_to_gpu:
            return {}

        def transform(addl_label: str, gpu_dict: Dict, *_):
            pci_id = pci_id_func(gpu_dict)
            return self._pci_to_gpu[pci_id].get('addl_labels', {}).get(addl_label)

        label_descs = {
            addl_label: {
                'transform': partial(transform, addl_label),
            } for addl_label in self._addl_labels
        }
        if value_path:
            for _, desc in label_descs.items():
                desc['path'] = value_path

        return label_descs

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
