from application.ports import EventBus
from application.read_models import PassengerStatsSummary, PassengerTiming
from application.repositories import PassengerStatsRepository
from domain.events import PassengerDroppedOff, PassengerPickedUp, RequestSubmitted
from domain.value_objects import PassengerId, Tick


class PassengerStatsProjection(PassengerStatsRepository):
    """Same seam as PositionLogProjection: in-memory today, but callers depend on
    PassengerStatsRepository, so a SQL-backed implementation could replace this without
    touching the orchestrator or the query handler."""

    def __init__(self, event_bus: EventBus) -> None:
        self._submitted_at: dict[PassengerId, Tick] = {}
        self._picked_up_at: dict[PassengerId, Tick] = {}
        self._dropped_off_at: dict[PassengerId, Tick] = {}
        event_bus.subscribe(RequestSubmitted, self._on_submitted)
        event_bus.subscribe(PassengerPickedUp, self._on_picked_up)
        event_bus.subscribe(PassengerDroppedOff, self._on_dropped_off)

    def _on_submitted(self, event: RequestSubmitted) -> None:
        self._submitted_at[event.passenger_id] = event.tick

    def _on_picked_up(self, event: PassengerPickedUp) -> None:
        self._picked_up_at[event.passenger_id] = event.tick

    def _on_dropped_off(self, event: PassengerDroppedOff) -> None:
        self._dropped_off_at[event.passenger_id] = event.tick

    def _timings(self) -> list[PassengerTiming]:
        return [
            PassengerTiming(
                passenger_id=passenger_id,
                submitted_at=submitted_at,
                picked_up_at=self._picked_up_at.get(passenger_id),
                dropped_off_at=self._dropped_off_at.get(passenger_id),
            )
            for passenger_id, submitted_at in self._submitted_at.items()
        ]

    def get_summary(self) -> PassengerStatsSummary:
        timings = self._timings()
        completed = [timing for timing in timings if timing.total_time is not None]
        still_in_progress_count = len(timings) - len(completed)
        if not completed:
            return PassengerStatsSummary(
                completed_count=0,
                still_in_progress_count=still_in_progress_count,
                min_wait_time=0,
                max_wait_time=0,
                avg_wait_time=0.0,
                min_total_time=0,
                max_total_time=0,
                avg_total_time=0.0,
            )
        wait_times = [timing.wait_time for timing in completed if timing.wait_time is not None]
        total_times = [timing.total_time for timing in completed if timing.total_time is not None]
        return PassengerStatsSummary(
            completed_count=len(completed),
            still_in_progress_count=still_in_progress_count,
            min_wait_time=min(wait_times),
            max_wait_time=max(wait_times),
            avg_wait_time=sum(wait_times) / len(wait_times),
            min_total_time=min(total_times),
            max_total_time=max(total_times),
            avg_total_time=sum(total_times) / len(total_times),
        )
