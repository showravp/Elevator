from domain.services.elevator_assigned import ElevatorAssigned
from domain.services.no_elevator_available import NoElevatorAvailable

SchedulingOutcome = ElevatorAssigned | NoElevatorAvailable
