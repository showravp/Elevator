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

## Workflow

- `main` is the default branch and stays deployable/clean. Bootstrapping/scaffolding commits
  (repo layout, tooling config, docs) go straight to `main`.
- All feature work (scheduler, simulation loop, CLI, tests, etc.) happens on a feature branch
  (`feature/<short-name>`) and merges into `main` via PR.
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
src/        simulation source code
README.md   run instructions, assumptions, trade-offs (kept current as the project evolves)
```
