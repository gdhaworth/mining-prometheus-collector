import os
import psutil
import sys
import time
import traceback

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from abstract_miner_collector import AbstractMinerCollector, NoSupportedMinerCollector
import trex_collector


class MiningCollector:
    @staticmethod
    def find_collector() -> AbstractMinerCollector:
        if 'DEBUG_MOCK_TREX' in os.environ:
            return trex_collector.instance()

        for proc in psutil.process_iter():
            try:
                name = proc.name().lower()
                if 't-rex' in name:
                    return trex_collector.instance()
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                traceback.print_exc()

        print('No miner found')  # TODO logger, stderr
        return NoSupportedMinerCollector()

    def collect(self):
        collector = self.find_collector()
        for metric in collector.collect():
            yield metric.metric


if __name__ == '__main__':
    REGISTRY.register(MiningCollector())
    start_http_server(32727)
    while True:
        time.sleep(1)
