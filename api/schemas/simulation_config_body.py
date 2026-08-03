from pydantic import BaseModel, Field

# Sanity upper bounds, not domain requirements — the take-home brief's "e.g., 1-10
# elevators" is illustrative, not a hard cap, so these are set generously higher just to
# reject obviously-absurd input (e.g. num_elevators: 100000) with a clean 422 instead of
# letting it run and fail asynchronously.
MAX_ELEVATORS = 50
MAX_FLOORS = 200
MAX_ELEVATOR_CAPACITY = 50


class SimulationConfigBody(BaseModel):
    """Used for both creating a run (POST /simulation-runs) and updating its config
    (PUT /simulation-runs/{id}/config) — same shape either way, only the guard on whether
    the update is currently allowed differs, and that lives in the route handler, not
    here."""

    num_elevators: int = Field(ge=1, le=MAX_ELEVATORS)
    num_floors: int = Field(ge=2, le=MAX_FLOORS)
    elevator_capacity: int = Field(ge=1, le=MAX_ELEVATOR_CAPACITY)
