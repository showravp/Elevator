from abc import ABC, abstractmethod

from application.read_models import PositionLogRow


class IPositionLogRepository(ABC):
    @abstractmethod
    def get_rows(self) -> list[PositionLogRow]: ...
