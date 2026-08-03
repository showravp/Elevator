from pathlib import Path

from application.read_models import PassengerStatsSummary
from application.simulation_run_id import SimulationRunId
from infrastructure.csv_passenger_stats_file_writer import CsvPassengerStatsFileWriter


def test_write_produces_a_metric_value_csv(tmp_path: Path) -> None:
    writer = CsvPassengerStatsFileWriter(output_dir=tmp_path)
    run_id = SimulationRunId("run-1")
    summary = PassengerStatsSummary(
        completed_count=2,
        still_in_progress_count=0,
        min_wait_time=1,
        max_wait_time=3,
        avg_wait_time=2.0,
        min_total_time=5,
        max_total_time=9,
        avg_total_time=7.0,
    )

    path = writer.write(run_id, summary)

    rows = Path(path).read_text(encoding="utf-8").splitlines()
    assert rows[0] == "metric,value"
    assert "completed_count,2" in rows
    assert "avg_total_time,7.0" in rows


def test_write_places_the_file_under_output_dir_run_id(tmp_path: Path) -> None:
    writer = CsvPassengerStatsFileWriter(output_dir=tmp_path)
    run_id = SimulationRunId("abc-123")
    summary = PassengerStatsSummary(0, 0, 0, 0, 0.0, 0, 0, 0.0)

    path = writer.write(run_id, summary)

    assert path == str(tmp_path / "abc-123" / "passenger_stats.csv")
