from application.exceptions import SimulationDidNotConvergeError
from application.outbox_relay import OutboxRelay
from application.ports import RequestSource
from application.repositories import ElevatorRepository, PassengerStatsRepository, RequestRepository
from domain.aggregates import Elevator, Request
from domain.value_objects import ElevatorId, Floor, Tick


class SimulationOrchestrator:
    def __init__(
        self,
        request_source: RequestSource,
        elevator_repository: ElevatorRepository,
        request_repository: RequestRepository,
        outbox_relay: OutboxRelay,
        passenger_stats_repository: PassengerStatsRepository,
        num_elevators: int,
        num_floors: int,
        elevator_capacity: int,
        max_ticks: int = 100_000,
    ) -> None:
        self._request_source = request_source
        self._elevator_repository = elevator_repository
        self._request_repository = request_repository
        self._outbox_relay = outbox_relay
        self._passenger_stats_repository = passenger_stats_repository
        self._num_elevators = num_elevators
        self._num_floors = num_floors
        self._elevator_capacity = elevator_capacity
        self._max_ticks = max_ticks

    def run(self) -> None:
        self._provision_elevators()
        self._outbox_relay.drain()
        # Tick 0 always runs, even with zero requests — idle elevators still occupy a
        # position at tick 0, and the position log must show every time step.
        tick = Tick(0)
        self._run_tick(tick)
        tick = tick.next()
        while self._has_unfinished_work():
            if tick.value > self._max_ticks:
                raise SimulationDidNotConvergeError(
                    f"simulation exceeded {self._max_ticks} ticks without all passengers "
                    "being delivered"
                )
            self._run_tick(tick)
            tick = tick.next()

    def _run_tick(self, tick: Tick) -> None:
        self._submit_due_requests(tick)
        self._advance_all_elevators(tick)
        self._outbox_relay.drain()

    def _provision_elevators(self) -> None:
        for index in range(self._num_elevators):
            elevator = Elevator.provision(
                elevator_id=ElevatorId(index),
                capacity=self._elevator_capacity,
                num_floors=self._num_floors,
                starting_floor=Floor(0),
                tick=Tick(0),
            )
            self._elevator_repository.save(elevator)

    def _submit_due_requests(self, tick: Tick) -> None:
        for raw in self._request_source.pop_due(tick):
            request = Request.submit(
                raw.passenger_id, raw.source, raw.destination, self._num_floors, raw.tick
            )
            self._request_repository.save(request)

    def _advance_all_elevators(self, tick: Tick) -> None:
        for elevator_id in self._elevator_repository.all_ids():
            elevator = self._elevator_repository.get(elevator_id)
            elevator.advance(tick)
            self._elevator_repository.save(elevator)

    def _has_unfinished_work(self) -> bool:
        return (
            self._request_source.has_more()
            or self._passenger_stats_repository.get_summary().still_in_progress_count > 0
        )
