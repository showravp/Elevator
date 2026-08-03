from abc import ABC, abstractmethod

from domain.aggregates import Elevator
from domain.value_objects import ElevatorId


class ElevatorRepository(ABC):
    @abstractmethod
    def get(self, elevator_id: ElevatorId) -> Elevator:
        """Raises AggregateNotFoundError if no such elevator has ever been saved."""

    @abstractmethod
    def save(self, elevator: Elevator) -> None:
        ...

    @abstractmethod
    def all_ids(self) -> list[ElevatorId]:
        ...
