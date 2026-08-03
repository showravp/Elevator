# CLAUDE.md

Context for Claude Code sessions working in this repo.

## What this is

A take-home project: simulate a destination-dispatch elevator bank in discrete time.
Passengers submit `time,id,source,dest` requests; a scheduler assigns each to a specific
elevator; the sim advances one floor-unit per tick. Requests must not be peeked at ahead of
their submission time.

Required outputs:
- Elevator position log: one row per time step, all elevator positions.
- Passenger summary stats: min/max/avg wait_time and total_time (`wait_time + travel_time`),
  plus any other notable observations.

Configurable: number of elevators, number of floors, max passengers per elevator.

Bonus (optional, not required): alternate scheduler algorithms (round robin, nearest-car,
zone-based), express elevators that skip floors, fairness-vs-efficiency trade-off analysis.

## Architecture

Clean Architecture + DDD + CQRS + event sourcing, deliberately, to demonstrate the pattern set
for the follow-up presentation — not because the problem size alone demands it. Key decisions:

- **Domain**: `Elevator` and `Request` are separate event-sourced aggregates (`AggregateRoot`
  base: `apply()`/`raise_event()`), each protecting only its own invariant (capacity/movement
  vs. no-double-assignment). No shared "Building" aggregate — the fleet is a plain collection.
- **CQRS-lite**: commands mutate aggregates and emit events; queries only ever read from
  projections (`PositionLogProjection`, `PassengerStatsProjection`), never the write model.
  In-process and synchronous — no message broker, no eventual consistency.
- **Outbox pattern**: `EventStore.append()` writes the aggregate stream and the outbox
  atomically (one in-memory call, no dual-write hazard by construction). `OutboxRelay.drain()`
  publishes to `EventBus` once per tick, *after* that tick's writes — deterministic ordering,
  no partial-tick projection state.
- **Cross-aggregate coordination**: `DispatchProcessManager` reacts to `RequestSubmitted`,
  runs `SchedulingPolicy`, then issues commands against both `Elevator` and `Request`.
- **Presentation**: REST API only (FastAPI), no CLI. `POST /simulations` is async —
  returns `202 {id, status}` via `BackgroundTasks`, results polled via `GET /simulations/{id}`
  and `GET /simulations/{id}/position-log` | `/passenger-stats`. Each run gets an isolated
  `EventStore`/`EventBus`/repositories/projections via a DI child scope, keyed in an
  in-memory `SimulationRegistry` (does not persist across server restarts).
- **DI**: `dependency-injector` library, used *only* in `composition/` — one registration
  module per layer (`domain_services.py`, `application_services.py`,
  `infrastructure_services.py`), composed in `composition/container.py`. Domain and
  application classes stay plain constructor-injected Python; no framework imports leak
  inward. Per-run isolation is a child container built by `composition/run_scope.py`.
- **File convention**: one class (including enums/exceptions) per `.py` file, with
  `__init__.py` re-exports per package for ergonomic imports. Exempt: FastAPI router modules
  and DI-wiring modules, which group functions, not classes — splitting those would fight
  the framework's own idiom rather than add clarity.

Build sequence (each its own `spodder/` branch): `domain-core` → `event-sourcing-infra` →
`api`, then bonus schedulers/express-elevators as later branches.

## Workflow

- `main` is the default branch and stays deployable/clean. Bootstrapping/scaffolding commits
  (repo layout, tooling config, docs) go straight to `main`.
- All feature work (scheduler, simulation loop, API, tests, etc.) happens on a feature branch
  (`spodder/<short-name>`) and merges into `main` via PR.
- Repo: https://github.com/showravp/Elevator (public).

## Environment notes

- Windows 11, PowerShell as primary shell, Bash tool also available.
- Python 3.13 is installed but was added to PATH *after* some existing shells started —
  if `python`/`git`/`gh` aren't found in a PowerShell call, prepend
  `C:\Program Files\Git\bin`, `C:\Program Files\GitHub CLI`, and
  `C:\Users\Showrav\AppData\Local\Programs\Python\Python313` to `$env:Path` for that call, or
  open a genuinely fresh terminal outside the tool session.
- Project virtualenv lives at `.venv/` (gitignored). Activate before running anything.
- `gh` is authenticated as `showravp` with git credential helper configured — pushes work
  without re-prompting.

## Repo layout

```
domain/          Elevator/Request aggregates, value objects, events, SchedulingPolicy — no I/O
application/     commands, queries, handlers, process manager, projections, ports, orchestrator
infrastructure/  in-memory event store/bus/registry, event-sourced repositories, CSV writers
api/             FastAPI app, routers, pydantic schemas — the only presentation layer
composition/     DI container + per-layer registration modules (dependency-injector)
tests/           mirrors the tree above
README.md        run instructions, assumptions, trade-offs (kept current as the project evolves)
```
