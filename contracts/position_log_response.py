from pydantic import BaseModel

from contracts.position_log_row_response import PositionLogRowResponse


class PositionLogResponse(BaseModel):
    status: str
    rows: list[PositionLogRowResponse]
