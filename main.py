import os
import pathlib
import psutil
import sys
import time
import traceback
import yaml

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from abstract_miner_collector import AbstractMinerCollector, NoSupportedMinerCollector
from trex_collector import TrexCollector
from lolminer_collector import LolminerCollector


class MiningCollector:
    def __init__(self):
        config_file = pathlib.Path(__file__).parent / 'config.yaml'
        if config_file.exists():
            with config_file.open('r') as f:
                self.config = yaml.full_load(f)
        else:
            self.config = None

        # from pprint import pprint
        # pprint(self.config)

    def find_collector(self) -> AbstractMinerCollector:
        if 'DEBUG_MOCK_TREX' in os.environ:
            return TrexCollector(self.config)
        elif 'DEBUG_MOCK_LOLMINER' in os.environ:
            return LolminerCollector(self.config)

        for proc in psutil.process_iter():
            try:
                name = proc.name().lower()
                if 't-rex' in name:
                    return TrexCollector(self.config)
                if 'lolminer' in name:
                    return LolminerCollector(self.config)
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
