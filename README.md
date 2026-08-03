# Elevator System Simulation

A discrete-time simulation of a destination-dispatch elevator system: passengers submit
origin + destination up front, a scheduler assigns each to an elevator, and the sim steps
forward one floor-time-unit at a time until every request is served.

Full spec: see the take-home brief this project implements (elevator bank, configurable
floors/elevators/capacity, wait-time and travel-time optimization, position log + summary
stats output).

Status: domain layer and event-sourcing infrastructure (store, outbox, repositories, dispatch
process manager, projections, orchestrator, DI composition root) are built and tested. No
runnable entry point yet — that lands with the REST API branch. See [CLAUDE.md](CLAUDE.md)
for the architecture and build sequence.

## Project layout

```
domain/          Elevator/Request aggregates, value objects, events, SchedulingPolicy — no I/O
application/     commands, queries, handlers, process manager, projections, ports, orchestrator
infrastructure/  in-memory event store/bus, event-sourced repositories, request source
composition/     DI container + per-layer registration modules (dependency-injector)
api/             FastAPI app, routers, pydantic schemas — not yet built
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
```

There's no CLI or API entry point yet — that's the next branch. For now, a full simulation
run is only reachable via `composition.container.build_application(...)` (see
`tests/composition/test_end_to_end_simulation.py` for a working example), or by running the
test suite:

```bash
pytest
```

## Time spent

TBD — tracked as the project progresses, filled in before final submission.

## Assumptions, simplifications, trade-offs

- **Intra-car stop ordering is greedy-nearest, not full SCAN/LOOK.** An elevator always
  moves toward whichever pending stop (pickup or drop-off) is closest by floor distance,
  not "continue in current direction until no more stops that way, then reverse." Simpler
  to reason about and test; a real destination-dispatch system would do better on average
  travel time with proper SCAN ordering.
- **Capacity is checked twice, deliberately.** `SchedulingPolicy` filters to elevators with
  headroom before choosing one (so assignment doesn't waste a pick on a full car), and
  `Elevator.schedule_stop()` independently re-checks and raises `CapacityExceededError` if
  violated — the aggregate protects its own invariant regardless of what the scheduler does,
  rather than trusting the caller.
- **A request with no available elevator is deferred, not retried on a fixed timer.** The
  dispatch process manager keeps it pending and retries whenever any elevator's occupancy
  changes (a passenger drops off), which is the only event that can free capacity.
- **CQRS is "lite" and event sourcing is real, but both scoped to a single in-process run.**
  No message broker, no eventual consistency — command handlers and the outbox relay run
  synchronously. See `CLAUDE.md` for the fuller rationale.

## What I'd improve with more time

- SCAN/LOOK-based intra-car ordering instead of greedy-nearest.
- Persist simulation runs (currently in-memory only, per `SimulationRegistry` design in
  `CLAUDE.md` — lost on server restart once the API lands).
- Bonus schedulers (round robin, zone-based) and express elevators, per the take-home's
  optional section.
