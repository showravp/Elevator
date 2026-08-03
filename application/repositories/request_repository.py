from abc import ABC, abstractmethod

from domain.aggregates import Request
from domain.value_objects import PassengerId


class IRequestRepository(ABC):
    @abstractmethod
    def get(self, passenger_id: PassengerId) -> Request:
        """Raises AggregateNotFoundException if no such request has ever been saved."""

    @abstractmethod
    def save(self, request: Request) -> None:
        ...
