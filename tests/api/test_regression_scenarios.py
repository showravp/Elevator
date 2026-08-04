from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def _client(output_dir: Path) -> TestClient:
    # TestClient runs BackgroundTasks synchronously, so the simulation has already
    # finished by the time .post() for /requests returns below — no polling needed.
    return TestClient(create_app(output_dir=output_dir))


def test_two_elevators_serve_three_passengers_across_a_100_floor_building(
    tmp_path: Path,
) -> None:
    # Regression scenario: a taller building (100 floors) than the fixtures used
    # elsewhere in this suite (typically 10), two passengers boarding at the same floor
    # and tick, and a third submitted mid-run at tick 10 traveling the opposite
    # direction. All three must still be served correctly.
    client = _client(tmp_path)
    config = {"num_elevators": 2, "num_floors": 100, "elevator_capacity": 5}

    create_response = client.post("/simulations", json=config)
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    requests = {
        "requests": [
            {"time": 0, "id": "pass1", "source": 1, "dest": 51},
            {"time": 0, "id": "pass2", "source": 1, "dest": 37},
            {"time": 10, "id": "pass3", "source": 20, "dest": 1},
        ]
    }
    submit_response = client.post(f"/simulations/{run_id}/requests", json=requests)
    assert submit_response.status_code == 202

    status_response = client.get(f"/simulations/{run_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    stats = client.get(f"/simulations/{run_id}/passenger-stats").json()
    assert stats["status"] == "completed"
    assert stats["completed_count"] == 3
    assert stats["still_in_progress_count"] == 0
    assert stats["min_wait_time"] >= 0
    assert stats["max_wait_time"] >= stats["min_wait_time"]
    assert stats["min_total_time"] >= 1  # travel is never instantaneous when source != dest
    assert stats["max_total_time"] >= stats["min_total_time"]
    assert stats["min_wait_time"] <= stats["avg_wait_time"] <= stats["max_wait_time"]
    assert stats["min_total_time"] <= stats["avg_total_time"] <= stats["max_total_time"]

    log_response = client.get(f"/simulations/{run_id}/position-log")
    assert log_response.status_code == 200
    rows = log_response.json()["rows"]
    assert len(rows) > 0
    assert {row["elevator_id"] for row in rows} == {0, 1}
    assert all(0 <= row["floor"] <= 99 for row in rows)

    assert (tmp_path / run_id / "config.csv").exists()
    assert (tmp_path / run_id / "position_log.csv").exists()
    assert (tmp_path / run_id / "passenger_stats.csv").exists()
