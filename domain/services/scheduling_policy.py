from abc import ABC, abstractmethod

from domain.aggregates import Elevator, Request
from domain.services.scheduling_outcome import SchedulingOutcome


class ISchedulingPolicy(ABC):
    @abstractmethod
    def select_elevator(self, request: Request, elevators: list[Elevator]) -> SchedulingOutcome:
        """ElevatorAssigned if a candidate has capacity, otherwise NoElevatorAvailable —
        an explicit outcome rather than Optional[Elevator], since a bare None here would
        be a service silently signaling "no capacity right now" with nothing in the type
        itself communicating what that means. The caller should keep the request pending
        and retry on a later tick when NoElevatorAvailable is returned."""
