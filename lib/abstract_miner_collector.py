import abc

from metric_wrappers import WrMetric
from typing import List


class AbstractMinerCollector(abc.ABC):
    @abc.abstractmethod
    def collect(self) -> List[WrMetric]:
        return []


class NoSupportedMinerCollector(AbstractMinerCollector):
    def collect(self) -> List[WrMetric]:
        return []
