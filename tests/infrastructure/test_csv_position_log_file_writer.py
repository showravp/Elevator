from pathlib import Path

from application.read_models import PositionLogRow
from application.simulation_run_id import SimulationRunId
from domain.value_objects import ElevatorId, Floor, Tick
from infrastructure.csv_position_log_file_writer import CsvPositionLogFileWriter


def _row(tick: int, elevator: int, floor: int) -> PositionLogRow:
    return PositionLogRow(tick=Tick(tick), elevator_id=ElevatorId(elevator), floor=Floor(floor))


def test_write_produces_a_wide_csv_with_one_row_per_tick(tmp_path: Path) -> None:
    writer = CsvPositionLogFileWriter(output_dir=tmp_path)
    run_id = SimulationRunId("run-1")
    rows = [
        _row(0, 0, 0),
        _row(0, 1, 0),
        _row(1, 0, 1),
        _row(1, 1, 0),
    ]

    path = writer.write(run_id, rows)

    content = Path(path).read_text(encoding="utf-8").splitlines()
    assert content[0] == "tick,elevator_0,elevator_1"
    assert content[1] == "0,0,0"
    assert content[2] == "1,1,0"


def test_write_places_the_file_under_output_dir_run_id(tmp_path: Path) -> None:
    writer = CsvPositionLogFileWriter(output_dir=tmp_path)
    run_id = SimulationRunId("abc-123")

    path = writer.write(run_id, [_row(0, 0, 0)])

    assert path == str(tmp_path / "abc-123" / "position_log.csv")
