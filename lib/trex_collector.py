import transformers

from abstract_miner_collector import AbstractMinerJsonCollector
from metric_wrappers import WrMetric

import platform

from collections import OrderedDict
from functools import cache, partial
from typing import List


xform_gpu_pci_id = partial(transformers.pcie_bus_slot_paths_to_id, 'pci_bus', 'pci_id')


MINER_LABELS = OrderedDict(
    host = {
        'transform': transformers.hostname,
    },
    platform = {
        'transform': transformers.mining_platform,
    },
    miner = {
        'value': 't-rex',
    },
    algorithm = {
        'path': 'algorithm',
    },
    worker = {
        'path': 'active_pool.worker',
    },
    pool_url = {
        'path': 'active_pool.url',
    },
    pool_user = {
        'path': 'active_pool.user',
    },
    paused = {
        'path': 'paused',
    },
    miner_version = {
        'path': 'version',
    },
    miner_version_build = {
        'path': 'revision',
    },
    miner_api_version = {
        'path': 'api',
    },
    miner_title = {
        'join': [
            'description',
            'version',
        ],
    }
)
MINER_COUNTER_METRICS = OrderedDict(
    uptime_sec = {
        'desc': 'amount of time miner has been running in seconds',
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
    hashrate = {
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
        'path': 'vendor',
    },
    device_name = {
        'path': 'name',
    },
    device_uuid = {
        'path': 'uuid',
    },
    device_pci_id = {
        'transform': xform_gpu_pci_id,
    },
    trex_potentially_unstable = {
        'path': 'potentially_unstable',
    },
    trex_device_id = {
        'path': 'device_id',
    },
    trex_gpu_id = {
        'path': 'gpu_id',
    },
    trex_gpu_user_id = {
        'path': 'gpu_user_id',
    },
    trex_low_load = {
        'path': 'low_load',
    },
    trex_lhr_tune = {
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
    gpu_hashrate = {
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
    gpu_power = {
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


class TrexCollector(AbstractMinerJsonCollector):
    @property
    @cache
    def api_url(self) -> str:
        running_linux = platform.system() == 'Linux'
        port = '3333' if running_linux else '4068'
        return f'http://127.0.0.1:{port}/summary'

    # TODO deduplicate code from lolminer
    def json_collect(self, request_time: float, json_data) -> List[WrMetric]:
        label_keys = list(MINER_LABELS.keys())
        metrics = self.create_counter_gauge_metrics(MINER_COUNTER_METRICS, MINER_GAUGE_METRICS, label_keys)
        labels = WrMetric.parse_label_values(json_data, MINER_LABELS)
        for metric in metrics:
            metric.add_value(base=json_data, labels=labels, timestamp=request_time)

        gpu_general_label_keys = list(label_keys)
        all_gpu_labels = OrderedDict(GPU_LABELS)
        all_gpu_labels.update(self.addl_gpu_labels_from_config(xform_gpu_pci_id))
        gpu_general_label_keys.extend(list(all_gpu_labels.keys()))

        gpu_metrics = self.create_counter_gauge_metrics(GPU_COUNTER_METRICS, GPU_GAUGE_METRICS, gpu_general_label_keys)
        for gpu in json_data['gpus']:
            gpu_labels = OrderedDict(labels)
            gpu_labels.update(WrMetric.parse_label_values(gpu, all_gpu_labels))
            for metric in gpu_metrics:
                metric.add_value(base=gpu, labels=gpu_labels, timestamp=request_time)
        metrics.extend(gpu_metrics)

        return metrics
