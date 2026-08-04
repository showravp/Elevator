import threading
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def _client(output_dir: Path) -> TestClient:
    # TestClient runs BackgroundTasks synchronously as part of the request/response
    # cycle, so by the time .post() for /requests returns, the simulation has already
    # finished running on that thread.
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

    # A real client gets a 202 back from POST /requests and is free to start polling
    # immediately, with no guarantee about whether the background run has finished yet.
    # Submit on its own thread and fire the three GET reads concurrently with it — none
    # of them may error, whichever side of "done" they happen to land on.
    def _submit() -> None:
        client.post(f"/simulations/{run_id}/requests", json=requests)

    submit_thread = threading.Thread(target=_submit)
    submit_thread.start()
    try:
        racing_status = client.get(f"/simulations/{run_id}")
        racing_stats = client.get(f"/simulations/{run_id}/passenger-stats")
        racing_log = client.get(f"/simulations/{run_id}/position-log")
    finally:
        submit_thread.join()

    assert racing_status.status_code == 200
    assert racing_status.json()["status"] in {"pending", "running", "completed"}
    assert racing_stats.status_code == 200
    assert racing_log.status_code == 200

    # Now that submission has definitely completed, assert the final, settled outcome.
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


def test_out_of_bounds_floor_requests_short_circuit_the_run(tmp_path: Path) -> None:
    # Negative regression: same passenger requests as the scenario above, but against a
    # much smaller 10-floor building — every one of them now names a floor that doesn't
    # exist (valid floors are 0..9; sources/dests of 51, 37, and 20 are all out of
    # range). The batch is still accepted at submission time — the contract layer only
    # checks source/dest are non-negative, since it has no notion of the run's floor
    # count — but Request.submit() validates floor bounds against num_floors before
    # raising any event, and ExecuteSimulationRunHandler treats that as fatal: the whole
    # run must short-circuit to a "failed" status as soon as it hits the first invalid
    # request, rather than silently dropping it or producing a partial/corrupted result.
    client = _client(tmp_path)
    config = {"num_elevators": 2, "num_floors": 10, "elevator_capacity": 10}

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
    body = status_response.json()
    assert body["status"] == "failed"
    assert body["error_message"] is not None
    assert "51" in body["error_message"]  # pass1 is first due at tick 0 — it trips first

    # The run stopped at the first invalid request it hit: pass2 and pass3 were never
    # even looked at, nothing was assigned or moved, and the required output files were
    # never written (only config.csv, persisted eagerly at run-creation time, exists).
    stats = client.get(f"/simulations/{run_id}/passenger-stats").json()
    assert stats["completed_count"] == 0
    assert stats["still_in_progress_count"] == 0

    log_rows = client.get(f"/simulations/{run_id}/position-log").json()["rows"]
    assert log_rows == []

    assert (tmp_path / run_id / "config.csv").exists()
    assert not (tmp_path / run_id / "position_log.csv").exists()
    assert not (tmp_path / run_id / "passenger_stats.csv").exists()
