from pydantic import BaseModel


class SimulationStatusResponse(BaseModel):
    run_id: str
    status: str
    error_message: str | None = None
