from pydantic import BaseModel


class PassengerStatsResponse(BaseModel):
    status: str
    completed_count: int
    still_in_progress_count: int
    min_wait_time: int
    max_wait_time: int
    avg_wait_time: float
    min_total_time: int
    max_total_time: int
    avg_total_time: float
