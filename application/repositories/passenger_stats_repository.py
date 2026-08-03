from abc import ABC, abstractmethod

from application.read_models import PassengerStatsSummary


class PassengerStatsRepository(ABC):
    @abstractmethod
    def get_summary(self) -> PassengerStatsSummary:
        ...
