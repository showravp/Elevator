from pydantic import BaseModel, model_validator

from api.schemas.request_dto import RequestDTO


class SubmitRequestsBody(BaseModel):
    requests: list[RequestDTO]

    @model_validator(mode="after")
    def _ids_must_be_unique(self) -> "SubmitRequestsBody":
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
