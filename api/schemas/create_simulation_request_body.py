from pydantic import BaseModel, Field, model_validator

from api.schemas.request_dto import RequestDTO

# Sanity upper bounds, not domain requirements — the take-home brief's "e.g., 1-10
# elevators" is illustrative, not a hard cap, so these are set generously higher just to
# reject obviously-absurd input (e.g. num_elevators: 100000) with a clean 422 instead of
# letting it run and fail asynchronously. Cross-field rules (source != dest, source/dest
# within num_floors) stay in the domain layer (Request.submit()) — duplicating them here
# would create a second source of truth.
MAX_ELEVATORS = 50
MAX_FLOORS = 200
MAX_ELEVATOR_CAPACITY = 50


class CreateSimulationRequestBody(BaseModel):
    num_elevators: int = Field(ge=1, le=MAX_ELEVATORS)
    num_floors: int = Field(ge=2, le=MAX_FLOORS)
    elevator_capacity: int = Field(ge=1, le=MAX_ELEVATOR_CAPACITY)
    requests: list[RequestDTO]

    @model_validator(mode="after")
    def _ids_must_be_unique(self) -> "CreateSimulationRequestBody":
        # Not a domain rule duplicated here — there's no existing domain-level protection
        # against two submissions sharing a passenger id; without this, the batch would
        # still fail, but deep in the event store as an opaque ConcurrencyConflictException
        # once the run is already in progress. Batch well-formedness belongs at the
        # boundary, before anything becomes a domain object.
        ids = [request.id for request in self.requests]
        if len(ids) != len(set(ids)):
            duplicates = sorted({id_ for id_ in ids if ids.count(id_) > 1})
            raise ValueError(f"duplicate passenger id(s) in requests: {duplicates}")
        return self
