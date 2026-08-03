from pydantic import BaseModel

from api.schemas.request_dto import RequestDTO


class CreateSimulationRequestBody(BaseModel):
    num_elevators: int
    num_floors: int
    elevator_capacity: int
    requests: list[RequestDTO]
