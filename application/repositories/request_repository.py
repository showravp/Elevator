from abc import ABC, abstractmethod

from domain.aggregates import Request
from domain.value_objects import PassengerId


class RequestRepository(ABC):
    @abstractmethod
    def get(self, passenger_id: PassengerId) -> Request:
        """Raises AggregateNotFoundError if no such request has ever been saved."""

    @abstractmethod
    def save(self, request: Request) -> None:
        ...
