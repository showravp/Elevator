from pydantic import BaseModel


class SimulationStatusResponse(BaseModel):
    id: str
    status: str
    error_message: str | None = None
