import csv
from pathlib import Path

from application.ports import IPassengerStatsFileWriter
from application.read_models import PassengerStatsSummary
from application.simulation_run_id import SimulationRunId


class CsvPassengerStatsFileWriter(IPassengerStatsFileWriter):
    def __init__(self, output_dir: Path = Path("output")) -> None:
        self._output_dir = output_dir

    def write(self, run_id: SimulationRunId, summary: PassengerStatsSummary) -> str:
        run_dir = self._output_dir / run_id.value
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "passenger_stats.csv"

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["metric", "value"])
            writer.writerow(["completed_count", summary.completed_count])
            writer.writerow(["still_in_progress_count", summary.still_in_progress_count])
            writer.writerow(["min_wait_time", summary.min_wait_time])
            writer.writerow(["max_wait_time", summary.max_wait_time])
            writer.writerow(["avg_wait_time", summary.avg_wait_time])
            writer.writerow(["min_total_time", summary.min_total_time])
            writer.writerow(["max_total_time", summary.max_total_time])
            writer.writerow(["avg_total_time", summary.avg_total_time])

        return str(path)
