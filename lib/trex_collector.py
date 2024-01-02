import transformers

from abstract_miner_collector import AbstractMinerCollector
from metric_wrappers import LookupType, WrMetric

import json
import os
import platform
import requests
import time
import traceback

from collections import OrderedDict
from functools import cache
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from typing import List


MINER_LABELS = OrderedDict(
    host = {
        'type': LookupType.CALLABLE,
        'func': transformers.hostname,
    },
    platform = {
        'type': LookupType.CALLABLE,
        'func': transformers.mining_platform,
    },
    miner = {
        'type': LookupType.DIRECT,
        'value': 't-rex',
    },
    algorithm = {
        'type': LookupType.VALUE_PATH,
        'path': 'algorithm',
    },
    worker = {
        'type': LookupType.VALUE_PATH,
        'path': 'active_pool.worker',
    },
    coin = {  # may be empty string
        'type': LookupType.VALUE_PATH,
        'path': 'coin',
    },
    pool_url = {
        'type': LookupType.VALUE_PATH,
        'path': 'active_pool.url',
    },
    pool_user = {
        'type': LookupType.VALUE_PATH,
        'path': 'active_pool.user',
    },
    paused = {
        'type': LookupType.VALUE_PATH,
        'path': 'paused',
    },
    miner_api_version = {
        'type': LookupType.VALUE_PATH,
        'path': 'api',
    },
    miner_version = {
        'type': LookupType.VALUE_PATH,
        'path': 'version',
    },
    miner_version_build = {
        'type': LookupType.VALUE_PATH,
        'path': 'revision',
    },
    driver_version = {
        'type': LookupType.VALUE_PATH,
        'path': 'driver',
    },
)
MINER_COUNTER_METRICS = OrderedDict(
    uptime = {
        'desc': 'amount of time miner has been running',
        'value_path': 'uptime',
    },
    shares_accepted = {
        'desc': 'number of accepted shares',
        'value_path': 'accepted_count',
    },
    shares_invalid = {
        'desc': 'number of invalid shares',
        'value_path': 'invalid_count',
    },
    shares_rejected = {
        'desc': 'number of rejected shares',
        'value_path': 'rejected_count',
    },
    solved_blocks = {
        'desc': 'count of solved blocks',
        'value_path': 'solved_count',
    },
)
MINER_GAUGE_METRICS = OrderedDict(
    gpu_count = {
        'desc': 'number of GPUs',
        'value_path': 'gpu_total',
    },
    hashrate_instant = {
        'desc': 'total hashrate',
        'value_path': 'hashrate',
    },
    hashrate_24h = {
        'desc': '1-day hashrate',
        'value_path': 'hashrate_day',
    },
    hashrate_1h = {
        'desc': '1-hour hashrate',
        'value_path': 'hashrate_hour',
    },
    hashrate_1m = {
        'desc': '1-minute hashrate',
        'value_path': 'hashrate_minute',
    },
    pool_difficulty = {
        'desc': 'pool work difficulty',
        'value_path': 'active_pool.difficulty',
        'transform': transformers.si_suffixed,
    },
    share_rate = {
        'desc': 'miner instant share rate',
        'value_path': 'sharerate',
    },
    share_rate_avg = {
        'desc': 'miner average share rate',
        'value_path': 'sharerate_average',
    },
)

GPU_LABELS = OrderedDict(
    device_vendor = {
        'type': LookupType.VALUE_PATH,
        'path': 'vendor',
    },
    device_name = {
        'type': LookupType.VALUE_PATH,
        'path': 'name',
    },
    device_uid = {
        'type': LookupType.VALUE_PATH,
        'path': 'uuid',
    },
    device_pci_bus = {
        'type': LookupType.VALUE_PATH,
        'path': 'pci_bus',
    },
    device_pci_domain = {
        'type': LookupType.VALUE_PATH,
        'path': 'pci_domain',
    },
    device_pci_id = {
        'type': LookupType.VALUE_PATH,
        'path': 'pci_id',
    },
    paused = {
        'type': LookupType.VALUE_PATH,
        'path': 'paused',
    },
    trex_potentially_unstable = {
        'type': LookupType.VALUE_PATH,
        'path': 'potentially_unstable',
    },
    trex_device_id = {
        'type': LookupType.VALUE_PATH,
        'path': 'device_id',
    },
    trex_gpu_id = {
        'type': LookupType.VALUE_PATH,
        'path': 'gpu_id',
    },
    trex_gpu_user_id = {
        'type': LookupType.VALUE_PATH,
        'path': 'gpu_user_id',
    },
    trex_low_load = {
        'type': LookupType.VALUE_PATH,
        'path': 'low_load',
    },
    trex_lhr_tune = {
        'type': LookupType.VALUE_PATH,
        'path': 'lhr_tune',
    },
)
GPU_COUNTER_METRICS = OrderedDict(
    gpu_shares_accepted = {
        'desc': 'Per-GPU accepted shares',
        'value_path': 'shares.accepted_count',
    },
    gpu_shares_invalid = {
        'desc': 'Per-GPU invalid shares',
        'value_path': 'shares.invalid_count',
    },
    gpu_shares_rejected = {
        'desc': 'Per-GPU rejected shares',
        'value_path': 'shares.rejected_count',
    },
    gpu_solved_blocks = {
        'desc': 'Number of blocks this GPU has solved',
        'value_path': 'shares.solved_count',
    },
    gpu_trex_lhr_lock_count = {
        'desc': 'Number of times the LHR lock has activated on the GPU',
        'value_path': 'lhr_lock_count',
    },
)
GPU_GAUGE_METRICS = OrderedDict(
    gpu_hashrate_instant = {
        'desc': 'GPU instantaneous total hashrate',
        'value_path': 'hashrate_instant',
    },
    gpu_hashrate_24h = {
        'desc': 'GPU 1-day hashrate',
        'value_path': 'hashrate_day',
    },
    gpu_hashrate_1h = {
        'desc': 'GPU 1-hour hashrate',
        'value_path': 'hashrate_hour',
    },
    gpu_hashrate_1m = {
        'desc': 'GPU 1-minute hashrate',
        'value_path': 'hashrate_minute',
    },
    gpu_hashrate_moment = {
        'desc': 'GPU hashrate',
        'value_path': 'hashrate',
    },
    gpu_clock_core = {
        'desc': 'GPU core clock speed',
        'value_path': 'cclock',
    },
    gpu_clock_memory = {
        'desc': 'GPU memory clock speed',
        'value_path': 'mclock',
    },
    gpu_mtweak = {
        'desc': 'GPU mtweak',
        'value_path': 'mtweak',
    },
    gpu_temperature_core = {
        'desc': 'GPU core temperature',
        'value_path': 'temperature',
    },
    gpu_fan_speed = {
        'desc': 'GPU fan speed',
        'value_path': 'fan_speed',
    },
    gpu_power_instant = {
        'desc': 'GPU power in watts',
        'value_path': 'power',
    },
    gpu_power_avg = {
        'desc': 'Average GPU power in watts',
        'value_path': 'power_avr',
    },
    gpu_intensity = {
        'desc': 'GPU mining intensity',
        'value_path': 'intensity',
    },
)


class TrexCollector(AbstractMinerCollector):
    def __init__(self):
        running_linux = platform.system() == 'Linux'
        port = '3333' if running_linux else '4068'
        self.api_url = f'http://127.0.0.1:{port}/summary'

    def _request_summary(self):
        mock_path = os.environ.get('DEBUG_MOCK_REQUEST', False)
        if mock_path:
            with open(mock_path, 'r') as f:
                return json.load(f)
        else:
            try:
                return requests.get(self.api_url).json()
            except:
                traceback.print_exc()
                return None

    def _create_metrics(self, metric_class, metric_descs, labels):
        return [WrMetric(
            metric_class=metric_class,
            name=name,
            labels=labels,
            **params,
        ) for name, params in metric_descs.items()]

    def _create_miner_metrics(self) -> List[WrMetric]:
        label_keys = list(MINER_LABELS.keys())
        metrics = self._create_metrics(CounterMetricFamily, MINER_COUNTER_METRICS, label_keys)
        metrics.extend(self._create_metrics(GaugeMetricFamily, MINER_GAUGE_METRICS, label_keys))
        return metrics

    def _create_gpu_metrics(self) -> List[WrMetric]:
        label_keys = list(MINER_LABELS.keys())
        label_keys.extend(GPU_LABELS.keys())
        metrics = self._create_metrics(CounterMetricFamily, GPU_COUNTER_METRICS, label_keys)
        metrics.extend(self._create_metrics(GaugeMetricFamily, GPU_GAUGE_METRICS, label_keys))
        return metrics

    def collect(self) -> List[WrMetric]:
        summary_time = time.time()
        summary = self._request_summary()
        # TODO better error handling
        if not summary:
            return []

        metrics = self._create_miner_metrics()
        labels = WrMetric.parse_label_values(summary, MINER_LABELS)
        for metric in metrics:
            metric.add_value(base=summary, labels=labels, timestamp=summary_time)

        gpu_metrics = self._create_gpu_metrics()
        for gpu in summary['gpus']:
            gpu_labels = OrderedDict(labels)
            gpu_labels.update(WrMetric.parse_label_values(gpu, GPU_LABELS))
            for metric in gpu_metrics:
                metric.add_value(base=gpu, labels=gpu_labels, timestamp=summary_time)
        metrics.extend(gpu_metrics)

        return metrics


@cache
def instance() -> AbstractMinerCollector:
    return TrexCollector()
