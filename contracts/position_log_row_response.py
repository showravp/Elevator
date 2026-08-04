from pydantic import BaseModel


class PositionLogRowResponse(BaseModel):
    tick: int
    elevator_id: int
    floor: int
