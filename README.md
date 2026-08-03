# Elevator System Simulation

A discrete-time simulation of a destination-dispatch elevator system: passengers submit
origin + destination up front, a scheduler assigns each to an elevator, and the sim steps
forward one floor-time-unit at a time until every request is served.

Full spec: see the take-home brief this project implements (elevator bank, configurable
floors/elevators/capacity, wait-time and travel-time optimization, position log + summary
stats output).

Status: repo scaffolding only — scheduler and simulation code land on feature branches per
[CLAUDE.md](CLAUDE.md).

## Project layout

```
src/        # simulation source code
```

## How to run

Requires Python 3.13.

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt   # once dependencies exist
python -m src.main <requests.csv> # entry point TBD
```

This section will be filled in once the simulation entry point exists.

## Assumptions, simplifications, trade-offs

TBD as the implementation progresses.

## What I'd improve with more time

TBD.
