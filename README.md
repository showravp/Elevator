# Elevator System Simulation

A discrete-time simulation of a destination-dispatch elevator system: passengers submit
origin + destination up front, a scheduler assigns each to an elevator, and the sim steps
forward one floor-time-unit at a time until every request is served.

Full spec: see the take-home brief this project implements (elevator bank, configurable
floors/elevators/capacity, wait-time and travel-time optimization, position log + summary
stats output).

Status: core simulation and REST API are built and tested end-to-end — domain layer,
event-sourcing infrastructure (store, outbox, repositories, dispatch process manager,
projections, orchestrator), DI composition root, and a FastAPI service exposing it.
`pyright --strict` and `ruff` both pass with zero errors.

## Project layout

```
domain/          Elevator/Request aggregates, value objects, events, ISchedulingPolicy,
                 aggregate repository interfaces — no I/O
application/     commands, queries, handlers, process manager, read models, read-side
                 repository interfaces, ports, orchestrator
infrastructure/  in-memory event store/bus/registry, event-sourced repositories, and the
                 projections (event-driven read-model writers) — swappable for a real DB
contracts/       request/response DTOs (pydantic models) — no dependency on any other layer
api/             FastAPI app, controllers, and the composition root that wires each layer's
                 own DI container together — the only presentation layer
tests/           mirrors the tree above
```

## How to run

Requires Python 3.13.

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt -r requirements-dev.txt
pip install -e .

uvicorn api.app:app --reload
```

Defaults to port 8000; pass `--port <N>` to use a different one, e.g.
`uvicorn api.app:app --reload --port 8080`.

Then open **http://127.0.0.1:8000/docs** (or your chosen port) for interactive Swagger UI
documentation of every
endpoint, or drive it directly:

Configuration and passenger requests are separate resources: create the run with its
config, then submit the request batch in a second call (config can be changed with a `PUT`
in between, but only before requests are submitted):

```bash
curl -X POST http://127.0.0.1:8000/simulations \
  -H "Content-Type: application/json" \
  -d '{"num_elevators": 2, "num_floors": 10, "elevator_capacity": 4}'
# -> {"id": "<run-id>", "status": "pending"}

curl -X POST http://127.0.0.1:8000/simulations/<run-id>/requests \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"time": 0, "id": "passenger1", "source": 1, "dest": 8},
      {"time": 3, "id": "passenger2", "source": 9, "dest": 1}
    ]
  }'
# -> {"id": "<run-id>", "status": "running"}

curl http://127.0.0.1:8000/simulations/<run-id>                    # status
curl http://127.0.0.1:8000/simulations/<run-id>/position-log        # required output 1
curl http://127.0.0.1:8000/simulations/<run-id>/passenger-stats     # required output 2
```

Simulations run in-memory in milliseconds, so by the time you poll, `status` is almost
always already `completed`. Run status lives only for the life of the server process — see
"What I'd improve with more time."

Test suite — `tests/` mirrors the source tree exactly: `tests/domain/` is pure unit tests
with no I/O, `tests/infrastructure/` covers every persistence adapter, `tests/api/` drives
the actual FastAPI app via `TestClient`:

```bash
pytest
```

Type checking and lint — strict mode, zero `Any` in the codebase:

```bash
pyright
ruff check .
```

## Time spent

TBD — tracked as the project progresses, filled in before final submission.

## Assumptions, simplifications, trade-offs

- **Intra-car stop ordering is greedy-nearest, not full SCAN/LOOK.** An elevator always
  moves toward whichever pending stop (pickup or drop-off) is closest by floor distance,
  not "continue in current direction until no more stops that way, then reverse." Simpler
  to reason about and test; a real destination-dispatch system would do better on average
  travel time with proper SCAN ordering.
- **Capacity is checked twice, deliberately.** `ISchedulingPolicy` filters to elevators with
  headroom before choosing one (so assignment doesn't waste a pick on a full car), and
  `Elevator.schedule_stop()` independently re-checks and raises `CapacityExceededException` if
  violated — the aggregate protects its own invariant regardless of what the scheduler does,
  rather than trusting the caller.
- **A request with no available elevator is deferred, not retried on a fixed timer.** The
  dispatch process manager keeps it pending and retries whenever any elevator's occupancy
  changes (a passenger drops off), which is the only event that can free capacity.
- **`None` is fine for aggregate/lifecycle state, not for services.** `Request` not yet
  being assigned an elevator, or a run not yet having failed, are legitimate `X | None`
  facts about that object's own state — mypy/pyright fully verify them, and they're never
  ambiguous about what they mean. A *service* returning a bare `Optional` is a different
  problem (the type alone doesn't say why), so `ISchedulingPolicy.select_elevator()`
  returns an explicit `ElevatorAssigned | NoElevatorAvailable` instead of `Elevator | None`.
- **CQRS is "lite" and event sourcing is real, but both scoped to a single in-process run.**
  No message broker, no eventual consistency — command handlers and the outbox relay run
  synchronously. See `CLAUDE.md` for the fuller rationale.
- **Configuration and passenger requests are separate resources.** A run can't serve
  requests without an established configuration, and configuration can't change once
  requests are submitted — enforced via status (`PUT /simulations/{id}/config` and
  `POST /simulations/{id}/requests` both 409 once the run is no longer `pending`) and via a
  config file (`output/<run-id>/config.csv`) that's the actual source of truth, not just an
  in-memory flag.
- **`POST /simulations/{id}/requests` accepts a full request batch, not a live stream.**
  The take-home's input is inherently "the whole request list, known up front, replayed
  through discrete time without peeking ahead" — the API models that as one call with the
  full batch (JSON, not the spec's literal CSV) rather than pretending requests arrive over
  real wall-clock time. "No peek ahead" is still enforced internally:
  `IRequestSource.pop_due(tick)` only ever exposes rows at or before the orchestrator's
  current tick.
- **Everything is in-memory, including run tracking.** No database — `ISimulationRegistry`
  and every run's event store live only for the life of the server process; restart loses
  all history. Deliberate for a take-home; would not survive contact with a real deployment.
- **No auth, no rate limiting.** Out of scope for the brief; noted so it doesn't read as an
  oversight.

## What I'd improve with more time

- SCAN/LOOK-based intra-car ordering instead of greedy-nearest.
- Persist simulation runs and event stores (SQLite or similar) so history survives a
  restart, and so `ISimulationRegistry` isn't a memory leak over a long-lived server process.
- Bonus schedulers (round robin, zone-based) and express elevators, per the take-home's
  optional section.
- A lightweight visualization (e.g. a chart of elevator positions over time) for the
  presentation, per the brief's "feel free to include visualizations" note.
