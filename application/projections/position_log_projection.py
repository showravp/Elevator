from application.ports import EventBus
from application.projections.position_log_row import PositionLogRow
from domain.events import ElevatorPositionRecorded


class PositionLogProjection:
    def __init__(self, event_bus: EventBus) -> None:
        self._rows: list[PositionLogRow] = []
        event_bus.subscribe(ElevatorPositionRecorded, self._on_position_recorded)

    def _on_position_recorded(self, event: ElevatorPositionRecorded) -> None:
        self._rows.append(
            PositionLogRow(tick=event.tick, elevator_id=event.elevator_id, floor=event.floor)
        )

    @property
    def rows(self) -> list[PositionLogRow]:
        return list(self._rows)
