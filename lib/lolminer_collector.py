import transformers

from abstract_miner_collector import AbstractMinerJsonCollector
from metric_wrappers import WrMetric

from collections import OrderedDict
from functools import partial
from typing import List


MINER_LABELS = OrderedDict(
    host = {
        'transform': transformers.hostname,
    },
    platform = {
        'transform': transformers.mining_platform,
    },
    miner = {
        'value': 'lolMiner',
    },
    algorithm = {
        'path': 'Algorithms[0].Algorithm',
    },
    worker = {
        'coalesce': [
            {
                'path': 'Algorithms[0].Worker',
            },
            {
                'path': 'Algorithms[0].User',
                'transform': transformers.worker_from_user_field,
            },
        ],
    },
    wallet = {
        'path': 'Algorithms[0].User',
        'transform': transformers.wallet_from_user_field,
    },
    pool_url = {
        'path': 'Algorithms[0].Pool'
    },
    pool_user = {
        'path': 'Algorithms[0].User',
    },
    miner_version = {
        'path': 'Software',
        'transform': lambda x: x.split(' ', 1)[-1],
    },
    miner_title = {
        'path': 'Software',
    }
)
MINER_COUNTER_METRICS = OrderedDict(
    uptime_sec = {
        'desc': 'amount of time miner has been running in seconds',
        'value_path': 'Session.Uptime',
    },
    shares_accepted = {
        'desc': 'number of accepted shares',
        'value_path': 'Algorithms[0].Total_Accepted',
    },
    shares_rejected = {
        'desc': 'number of rejected shares',
        'value_path': 'Algorithms[0].Total_Rejected',
    },
    shares_stale = {
        'desc': 'number of stale shares',
        'value_path': 'Algorithms[0].Total_Stales',
    },
    shares_error = {
        'desc': 'number of error shares',
        'value_path': 'Algorithms[0].Total_Errors',
    },
)
MINER_GAUGE_METRICS = OrderedDict(
    gpu_count = {
        'desc': 'number of GPUs',
        'value_path': 'Num_Workers',
    },
    hashrate = {
        'desc': 'total hashrate',
        'value_path': 'Algorithms[0]',
        'transform': partial(transformers.pow10, 'Total_Performance', 'Performance_Factor'),
    },
)

GPU_LABELS = OrderedDict(
    device_vendor = {
        'path': 'Workers[i].Name',
        'transform': lambda x: x.split(' ', 1)[0],
    },
    device_name = {
        'path': 'Workers[i].Name',
    },
    device_pci_id = {
        'path': 'Workers[i].PCIE_Address',
        'transform': transformers.pcie_bus_slot_str_to_id,
    }
)
GPU_COUNTER_METRICS = OrderedDict(
    gpu_shares_accepted = {
        'desc': 'Per-GPU accepted shares',
        'value_path': 'Algorithms[0].Worker_Accepted[i]',
    },
    gpu_shares_rejected = {
        'desc': 'Per-GPU rejected shares',
        'value_path': 'Algorithms[0].Worker_Rejected[i]',
    },
    gpu_shares_stale = {
        'desc': 'Per-GPU stale shares',
        'value_path': 'Algorithms[0].Worker_Stales[i]',
    },
    gpu_shares_error = {
        'desc': 'Per-GPU error shares',
        'value_path': 'Algorithms[0].Worker_Errors[i]',
    },
)
GPU_GAUGE_METRICS = OrderedDict(
    gpu_hashrate = {
        'desc': 'GPU hashrate',
        'value_path': 'Algorithms[0]',
        'transform': partial(transformers.pow10, 'Worker_Performance[i]', 'Performance_Factor'),
    },
    gpu_clock_core = {
        'desc': 'GPU core clock speed',
        'value_path': 'Workers[i].CCLK',
        'transform': transformers.mul(1000 * 1000),
    },
    gpu_clock_memory = {
        'desc': 'GPU memory clock speed',
        'value_path': 'Workers[i].MCLK',
        'transform': transformers.mul(1000 * 1000),
    },
    gpu_temperature_core = {
        'desc': 'GPU core temperature',
        'value_path': 'Workers[i].Core_Temp',
        'transform': transformers.only_above_0,
    },
    gpu_temperature_junction = {
        'desc': 'GPU junction temperature',
        'value_path': 'Workers[i].Juc_Temp',
        'transform': transformers.only_above_0,
    },
    gpu_temperature_memory = {
        'desc': 'GPU memory temperature',
        'value_path': 'Workers[i].Mem_Temp',
        'transform': transformers.only_above_0,
    },
    gpu_fan_speed = {
        'desc': 'GPU fan speed',
        'value_path': 'Workers[i].Fan_Speed',
    },
    gpu_power = {
        'desc': 'GPU power in watts',
        'value_path': 'Workers[i].Power',
    },
)


class LolminerCollector(AbstractMinerJsonCollector):
    @property
    def api_url(self):
        return 'http://127.0.0.1:3333/'

    def json_collect(self, request_time: float, json_data) -> List[WrMetric]:
        label_keys = list(MINER_LABELS.keys())
        metrics = self.create_counter_gauge_metrics(MINER_COUNTER_METRICS, MINER_GAUGE_METRICS, label_keys)
        labels = WrMetric.parse_label_values(json_data, MINER_LABELS)
        for metric in metrics:
            metric.add_value(base=json_data, labels=labels, timestamp=request_time)

        gpu_general_label_keys = list(label_keys)
        all_gpu_labels = OrderedDict(GPU_LABELS)
        all_gpu_labels.update(self.addl_gpu_labels_from_config(transformers.pcie_bus_slot_str_to_id,
                                                               'Workers[i].PCIE_Address'))
        gpu_general_label_keys.extend(list(all_gpu_labels.keys()))

        gpu_metrics = self.create_counter_gauge_metrics(GPU_COUNTER_METRICS, GPU_GAUGE_METRICS, gpu_general_label_keys)
        for i in range(len(json_data['Workers'])):
            gpu_labels = OrderedDict(labels)
            gpu_labels.update(WrMetric.parse_label_values(json_data, all_gpu_labels, i))
            for metric in gpu_metrics:
                metric.add_value(base=json_data, labels=gpu_labels, timestamp=request_time, i=i)
        metrics.extend(gpu_metrics)

        return metrics
