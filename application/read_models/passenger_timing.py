from dataclasses import dataclass

from domain.value_objects import PassengerId, Tick


@dataclass(frozen=True, slots=True)
class PassengerTiming:
    passenger_id: PassengerId
    submitted_at: Tick
    picked_up_at: Tick | None
    dropped_off_at: Tick | None

    @property
    def wait_time(self) -> int | None:
        if self.picked_up_at is None:
            return None
        return self.picked_up_at.value - self.submitted_at.value

    @property
    def travel_time(self) -> int | None:
        if self.picked_up_at is None or self.dropped_off_at is None:
            return None
        return self.dropped_off_at.value - self.picked_up_at.value

    @property
    def total_time(self) -> int | None:
        if self.dropped_off_at is None:
            return None
        return self.dropped_off_at.value - self.submitted_at.value
