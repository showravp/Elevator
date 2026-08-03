from application.projections import PositionLogProjection
from domain.events import ElevatorPositionRecorded
from domain.value_objects import Direction, ElevatorId, Floor, Tick
from infrastructure.in_memory_event_bus import InMemoryEventBus


def test_rows_accumulate_one_per_position_recorded_event() -> None:
    bus = InMemoryEventBus()
    projection = PositionLogProjection(bus)

    bus.publish(
        ElevatorPositionRecorded(
            elevator_id=ElevatorId(0), floor=Floor(0), direction=Direction.IDLE, tick=Tick(0)
        )
    )
    bus.publish(
        ElevatorPositionRecorded(
            elevator_id=ElevatorId(0), floor=Floor(1), direction=Direction.UP, tick=Tick(1)
        )
    )
    bus.publish(
        ElevatorPositionRecorded(
            elevator_id=ElevatorId(1), floor=Floor(0), direction=Direction.IDLE, tick=Tick(1)
        )
    )

    rows = projection.rows
    assert len(rows) == 3
    assert (rows[1].elevator_id, rows[1].floor, rows[1].tick) == (ElevatorId(0), Floor(1), Tick(1))
