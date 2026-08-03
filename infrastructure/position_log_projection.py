from application.ports import IEventBus
from application.read_models import PositionLogRow
from application.repositories import IPositionLogRepository
from domain.events import ElevatorPositionRecorded


class PositionLogProjection(IPositionLogRepository):
    """Event-driven read model, in-memory today. If this ever moved behind a real
    database, this class is the piece that would write rows into a table on each event —
    get_rows() is the seam a SQL-backed implementation would replace, and callers (query
    handlers, the orchestrator) depend only on IPositionLogRepository, never on this class."""

    def __init__(self, event_bus: IEventBus) -> None:
        self._rows: list[PositionLogRow] = []
        event_bus.subscribe(ElevatorPositionRecorded, self._on_position_recorded)

    def _on_position_recorded(self, event: ElevatorPositionRecorded) -> None:
        self._rows.append(
            PositionLogRow(tick=event.tick, elevator_id=event.elevator_id, floor=event.floor)
        )

    def get_rows(self) -> list[PositionLogRow]:
        return list(self._rows)
