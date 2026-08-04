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
  Their repository interfaces (`IElevatorRepository`, `IRequestRepository`,
  `domain/repositories/`) live in `domain/` too, not `application/` — Evans' original DDD
  placement, since a repository is how the domain model expresses "give me one of these
  aggregates back," independent of persistence technology. This only holds for genuine
  aggregate repositories; `IPositionLogRepository`/`IPassengerStatsRepository`/
  `IConfigRepository` (`application/repositories/`) depend on application-layer DTOs
  (`PositionLogRow`, `SimulationConfig`, ...) and aren't aggregate-consistency boundaries at
  all — moving them to `domain/` would violate the Dependency Rule, so they stay put.
- **CQRS-lite**: commands mutate aggregates and emit events; queries only ever read from
  read models via repository ports (`IPositionLogRepository`, `IPassengerStatsRepository`),
  never the write model. The event-driven writers of those read models
  (`PositionLogProjection`, `PassengerStatsProjection`) live in `infrastructure/`, not
  `application/` — they're the swappable-for-a-real-database piece, same as an ORM-backed
  repository would be. Application code (query handlers, `SimulationOrchestrator`) depends
  only on the port, never on these concrete classes. In-process and synchronous — no
  message broker, no eventual consistency.
- **Outbox pattern**: `IEventStore.append()` writes the aggregate stream and the outbox
  atomically (one in-memory call, no dual-write hazard by construction). `OutboxRelay.drain()`
  publishes to `IEventBus` once per tick, *after* that tick's writes — deterministic ordering,
  no partial-tick projection state.
- **Cross-aggregate coordination**: `DispatchProcessManager` reacts to `RequestSubmitted`,
  runs `ISchedulingPolicy`, then issues commands against both `Elevator` and `Request`.
- **Presentation**: REST API only (FastAPI), no CLI. `POST /simulations` is async —
  returns `202 {id, status}` via `BackgroundTasks`, results polled via `GET /simulations/{id}`
  and `GET /simulations/{id}/position-log` | `/passenger-stats`. Each run gets an isolated
  `IEventStore`/`IEventBus`/repositories/read models via a DI child scope, keyed in an
  in-memory `ISimulationRegistry` (does not persist across server restarts). Request/response
  DTOs live in a separate top-level `contracts/` package, not in `api/` and not in `domain/`
  — mirroring a .NET solution splitting request/response models into their own `Contracts`
  project (e.g. so a client SDK could depend on just the wire shapes without pulling in the
  whole Web API). `contracts/` has zero imports from any other layer — only `api/`
  (specifically `api/controllers/`) depends on it, converting between contracts and
  domain/application types (e.g. `SimulationConfigBody` → `SimulationConfig`) at the
  controller boundary; that conversion logic stays in `api/`, not in `contracts/` itself.
- **DI**: `dependency-injector` library. Each layer owns its own DI registration file —
  `domain/dependency_injection.py` (`DomainServicesContainer`),
  `application/dependency_injection.py` (`ApplicationServicesContainer`),
  `infrastructure/dependency_injection.py` (`InfrastructureServicesContainer`) — mirroring
  the .NET convention of a `DependencyInjection.cs` per project, rather than centralizing
  all container definitions in one place. There is no separate `composition/` package —
  the composition root lives directly in `api/`, split across four files the same way a
  .NET minimal-API project splits `Program.cs`-equivalent responsibilities:
  `api/program.py`'s `build_application()` builds the per-run object graph (constructs
  `InfrastructureServicesContainer` and wires its concrete instances into
  `ApplicationServicesContainer`'s `providers.Dependency(instance_of=...)` slots);
  `api/run_scope.py`'s `RunScope` tracks per-run container lifecycle (kept in its own file,
  not folded into `program.py`, because it's a genuine class — the one-class-per-file rule
  below still applies to it; folding it in would also create a real import cycle, since
  `RunScope` needs `build_application` and `bootstrap_api_state` needs `RunScope`'s type —
  the acyclic order is `program.py` → `run_scope.py` → `app.py`); `api/app.py`'s
  `bootstrap_api_state()` builds the one process-wide `ISimulationRegistry`/`RunScope`/
  status handler, and its `create_app()` assembles the FastAPI app — genuinely the same
  file .NET's `Program.cs` would be, since minimal APIs bundle "register services" and
  "configure the app" together; `api/services.py` holds the `Depends()` provider functions
  (FastAPI's equivalent of resolving from `IServiceProvider`). `ApplicationServicesContainer`
  itself never imports `infrastructure` — every port it needs but can't construct is a typed
  `Dependency` slot, supplied from `api/program.py`, so the Dependency Rule holds for the DI
  wiring files exactly as strictly as for the rest of the app. (It *does* import
  `domain/dependency_injection.py` directly — application depending on domain, the allowed
  direction.) Within `api/`, only `program.py` and `app.py` import `infrastructure`
  directly — controllers never do, same separation as before, just enforced by file
  boundary within one package instead of by a separate package; this mirrors how
  Controllers in a .NET Web API project never reference Infrastructure concrete types even
  though `Program.cs`, in the same project, does. Pyright's dependency-injector
  stub-quality relaxation (`reportUnknownMemberType`) is scoped file-by-file in
  `pyproject.toml` to wherever a `Provider[Unknown]` actually surfaces, not blanket per
  layer — currently just `application/dependency_injection.py`'s nested-container attribute
  access (`domain.scheduling_policy`).
- **File convention**: one class (including enums/exceptions) per `.py` file, with
  `__init__.py` re-exports per package for ergonomic imports. Exempt: FastAPI controller
  modules and DI-wiring modules, which group functions, not classes — splitting those would
  fight the framework's own idiom rather than add clarity. `contracts/` follows the normal
  rule (one Pydantic model per file) since each is a genuine class.

Build sequence (each its own `spodder/` branch): `domain-core` → `event-sourcing-infra` →
`api` → `read-repository-pattern` (audit fix: query handlers and the orchestrator were
depending on concrete projection classes instead of repository ports; `api/app.py` was
also constructing infrastructure directly instead of going through the composition root) →
`clean-architecture-di` (aggregate repository interfaces moved to `domain/`; DI
registration moved from a separate `composition/` package into a `dependency_injection.py`
per layer, composition root folded into `api/` as `program.py`/`run_scope.py`/`app.py`/
`services.py`; request/response DTOs extracted from `api/schemas/` into a new top-level
`contracts/` package; `api/routers/` renamed to `api/controllers/`), then bonus
schedulers/express-elevators as later branches.

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
domain/          Elevator/Request aggregates, value objects, events, ISchedulingPolicy,
                 aggregate repository interfaces (IElevatorRepository/IRequestRepository),
                 own DI registration (dependency_injection.py) — no I/O
application/     commands, queries, handlers, process manager, read models (DTOs), ports,
                 read-side + config repository interfaces, orchestrator, own DI registration
                 (dependency_injection.py) — depends only on domain/, never infrastructure/
infrastructure/  in-memory event store/bus/registry, event-sourced repositories, the
                 projections (event-driven read-model writers), own DI registration
                 (dependency_injection.py) — all swappable for a real database without
                 touching application/ or domain/
contracts/       request/response DTOs (pydantic models) — no dependency on any other
                 layer; only api/controllers/ depends on it
api/             FastAPI app, controllers, AND the composition root (program.py/
                 run_scope.py/app.py/services.py) — the only presentation layer, and the
                 only place infrastructure gets constructed; no separate composition/
                 package, same as a .NET Web API project's Program.cs
tests/           mirrors the tree above
README.md        run instructions, assumptions, trade-offs (kept current as the project evolves)
```
