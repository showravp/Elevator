from abc import ABC, abstractmethod

from domain.aggregates import Elevator
from domain.value_objects import ElevatorId


class IElevatorRepository(ABC):
    @abstractmethod
    def get(self, elevator_id: ElevatorId) -> Elevator:
        """Raises AggregateNotFoundException if no such elevator has ever been saved."""

    @abstractmethod
    def save(self, elevator: Elevator) -> None: ...

    @abstractmethod
    def all_ids(self) -> list[ElevatorId]: ...
