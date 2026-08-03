from abc import ABC, abstractmethod

from application.read_models import PositionLogRow


class PositionLogRepository(ABC):
    @abstractmethod
    def get_rows(self) -> list[PositionLogRow]:
        ...
