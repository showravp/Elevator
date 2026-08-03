from abc import ABC, abstractmethod

from domain.aggregates import Elevator, Request


class SchedulingPolicy(ABC):
    @abstractmethod
    def select_elevator(self, request: Request, elevators: list[Elevator]) -> Elevator | None:
        """Choose the best elevator for `request`, or None if none currently has capacity
        (caller should keep the request pending and retry on a later tick)."""
