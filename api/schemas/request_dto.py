from pydantic import BaseModel


class RequestDTO(BaseModel):
    """Field names match the take-home spec's CSV columns (time,id,source,dest) so the
    JSON body is self-documenting relative to the brief."""

    time: int
    id: str
    source: int
    dest: int
