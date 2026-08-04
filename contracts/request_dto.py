from pydantic import BaseModel, Field


class RequestDTO(BaseModel):
    """Field names match the take-home spec's CSV columns (time,id,source,dest) so the
    JSON body is self-documenting relative to the brief."""

    time: int = Field(ge=0)
    id: str = Field(min_length=1)
    source: int = Field(ge=0)
    dest: int = Field(ge=0)
