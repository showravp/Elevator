from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def _client(output_dir: Path) -> TestClient:
    # TestClient runs BackgroundTasks synchronously as part of the request/response
    # cycle, so by the time .post() returns, the simulation has already finished running
    # — no polling needed in these tests. output_dir is redirected to a pytest tmp_path so
    # these tests never write into the real repo's output/ directory.
    return TestClient(create_app(output_dir=output_dir))


def test_create_and_complete_simulation_end_to_end(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {
        "num_elevators": 2,
        "num_floors": 10,
        "elevator_capacity": 4,
        "requests": [
            {"time": 0, "id": "p1", "source": 0, "dest": 5},
            {"time": 0, "id": "p2", "source": 3, "dest": 9},
        ],
    }

    create_response = client.post("/simulations", json=payload)
    assert create_response.status_code == 202
    run_id = create_response.json()["id"]

    status_response = client.get(f"/simulations/{run_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    stats_response = client.get(f"/simulations/{run_id}/passenger-stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["completed_count"] == 2
    assert stats["still_in_progress_count"] == 0
    assert stats["status"] == "completed"

    log_response = client.get(f"/simulations/{run_id}/position-log")
    assert log_response.status_code == 200
    rows = log_response.json()["rows"]
    assert len(rows) > 0
    assert {row["elevator_id"] for row in rows} == {0, 1}

    assert (tmp_path / run_id / "position_log.csv").exists()
    assert (tmp_path / run_id / "passenger_stats.csv").exists()


def test_get_status_for_unknown_run_returns_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/simulations/does-not-exist")

    assert response.status_code == 404


def test_get_position_log_for_unknown_run_returns_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/simulations/does-not-exist/position-log")

    assert response.status_code == 404


def test_create_simulation_rejects_zero_elevators(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 0, "num_floors": 10, "elevator_capacity": 4, "requests": []}

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_absurdly_many_elevators(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 100_000, "num_floors": 10, "elevator_capacity": 4, "requests": []}

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_single_floor_building(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 1, "num_floors": 1, "elevator_capacity": 4, "requests": []}

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_negative_request_fields(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {
        "num_elevators": 1,
        "num_floors": 10,
        "elevator_capacity": 4,
        "requests": [{"time": -1, "id": "p1", "source": 0, "dest": 5}],
    }

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_empty_passenger_id(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {
        "num_elevators": 1,
        "num_floors": 10,
        "elevator_capacity": 4,
        "requests": [{"time": 0, "id": "", "source": 0, "dest": 5}],
    }

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_duplicate_passenger_ids(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {
        "num_elevators": 1,
        "num_floors": 10,
        "elevator_capacity": 4,
        "requests": [
            {"time": 0, "id": "p1", "source": 0, "dest": 5},
            {"time": 1, "id": "p1", "source": 2, "dest": 7},
        ],
    }

    response = client.post("/simulations", json=payload)

    assert response.status_code == 422
    assert "duplicate" in response.text.lower()


def test_two_concurrent_runs_stay_isolated(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload_a = {
        "num_elevators": 1,
        "num_floors": 10,
        "elevator_capacity": 2,
        "requests": [{"time": 0, "id": "a1", "source": 0, "dest": 4}],
    }
    payload_b = {
        "num_elevators": 1,
        "num_floors": 10,
        "elevator_capacity": 2,
        "requests": [
            {"time": 0, "id": "b1", "source": 0, "dest": 4},
            {"time": 0, "id": "b2", "source": 1, "dest": 6},
        ],
    }

    run_a = client.post("/simulations", json=payload_a).json()["id"]
    run_b = client.post("/simulations", json=payload_b).json()["id"]

    stats_a = client.get(f"/simulations/{run_a}/passenger-stats").json()
    stats_b = client.get(f"/simulations/{run_b}/passenger-stats").json()

    assert stats_a["completed_count"] == 1
    assert stats_b["completed_count"] == 2
