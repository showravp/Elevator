from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app

_CONFIG_PAYLOAD = {"num_elevators": 2, "num_floors": 10, "elevator_capacity": 4}


def _client(output_dir: Path) -> TestClient:
    # TestClient runs BackgroundTasks synchronously as part of the request/response
    # cycle, so by the time .post() for /requests returns, the simulation has already
    # finished running — no polling needed in these tests. output_dir is redirected to a
    # pytest tmp_path so these tests never write into the real repo's output/ directory.
    return TestClient(create_app(output_dir=output_dir))


def _create_run(client: TestClient, config: dict[str, int] = _CONFIG_PAYLOAD) -> str:
    response = client.post("/simulation-runs", json=config)
    assert response.status_code == 201
    run_id: str = response.json()["run_id"]
    return run_id


def test_create_and_complete_simulation_end_to_end(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    requests = {
        "requests": [
            {"time": 0, "id": "p1", "source": 0, "dest": 5},
            {"time": 0, "id": "p2", "source": 3, "dest": 9},
        ]
    }

    submit_response = client.post(f"/simulation-runs/{run_id}/requests", json=requests)
    assert submit_response.status_code == 202

    status_response = client.get(f"/simulation-runs/{run_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    stats_response = client.get(f"/simulation-runs/{run_id}/passenger-stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["completed_count"] == 2
    assert stats["still_in_progress_count"] == 0
    assert stats["status"] == "completed"

    log_response = client.get(f"/simulation-runs/{run_id}/position-log")
    assert log_response.status_code == 200
    rows = log_response.json()["rows"]
    assert len(rows) > 0
    assert {row["elevator_id"] for row in rows} == {0, 1}

    assert (tmp_path / run_id / "config.csv").exists()
    assert (tmp_path / run_id / "position_log.csv").exists()
    assert (tmp_path / run_id / "passenger_stats.csv").exists()


def test_get_status_for_unknown_run_returns_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/simulation-runs/does-not-exist")

    assert response.status_code == 404


def test_get_position_log_for_unknown_run_returns_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/simulation-runs/does-not-exist/position-log")

    assert response.status_code == 404


def test_create_simulation_rejects_zero_elevators(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 0, "num_floors": 10, "elevator_capacity": 4}

    response = client.post("/simulation-runs", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_absurdly_many_elevators(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 100_000, "num_floors": 10, "elevator_capacity": 4}

    response = client.post("/simulation-runs", json=payload)

    assert response.status_code == 422


def test_create_simulation_rejects_single_floor_building(tmp_path: Path) -> None:
    client = _client(tmp_path)
    payload = {"num_elevators": 1, "num_floors": 1, "elevator_capacity": 4}

    response = client.post("/simulation-runs", json=payload)

    assert response.status_code == 422


def test_submit_requests_rejects_negative_request_fields(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    requests = {"requests": [{"time": -1, "id": "p1", "source": 0, "dest": 5}]}

    response = client.post(f"/simulation-runs/{run_id}/requests", json=requests)

    assert response.status_code == 422


def test_submit_requests_rejects_empty_passenger_id(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    requests = {"requests": [{"time": 0, "id": "", "source": 0, "dest": 5}]}

    response = client.post(f"/simulation-runs/{run_id}/requests", json=requests)

    assert response.status_code == 422


def test_submit_requests_rejects_duplicate_passenger_ids(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    requests = {
        "requests": [
            {"time": 0, "id": "p1", "source": 0, "dest": 5},
            {"time": 1, "id": "p1", "source": 2, "dest": 7},
        ]
    }

    response = client.post(f"/simulation-runs/{run_id}/requests", json=requests)

    assert response.status_code == 422
    assert "duplicate" in response.text.lower()


def test_two_concurrent_runs_stay_isolated(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_a = _create_run(client, {"num_elevators": 1, "num_floors": 10, "elevator_capacity": 2})
    run_b = _create_run(client, {"num_elevators": 1, "num_floors": 10, "elevator_capacity": 2})

    client.post(
        f"/simulation-runs/{run_a}/requests",
        json={"requests": [{"time": 0, "id": "a1", "source": 0, "dest": 4}]},
    )
    client.post(
        f"/simulation-runs/{run_b}/requests",
        json={
            "requests": [
                {"time": 0, "id": "b1", "source": 0, "dest": 4},
                {"time": 0, "id": "b2", "source": 1, "dest": 6},
            ]
        },
    )

    stats_a = client.get(f"/simulation-runs/{run_a}/passenger-stats").json()
    stats_b = client.get(f"/simulation-runs/{run_b}/passenger-stats").json()

    assert stats_a["completed_count"] == 1
    assert stats_b["completed_count"] == 2


def test_update_config_while_pending_succeeds(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    new_config = {"num_elevators": 3, "num_floors": 20, "elevator_capacity": 8}

    response = client.put(f"/simulation-runs/{run_id}/config", json=new_config)

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_update_config_after_requests_submitted_returns_409(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    client.post(
        f"/simulation-runs/{run_id}/requests",
        json={"requests": [{"time": 0, "id": "p1", "source": 0, "dest": 5}]},
    )

    response = client.put(f"/simulation-runs/{run_id}/config", json=_CONFIG_PAYLOAD)

    assert response.status_code == 409


def test_submit_requests_twice_returns_409(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run_id = _create_run(client)
    first_requests = {"requests": [{"time": 0, "id": "p1", "source": 0, "dest": 5}]}
    client.post(f"/simulation-runs/{run_id}/requests", json=first_requests)

    response = client.post(f"/simulation-runs/{run_id}/requests", json=first_requests)

    assert response.status_code == 409
