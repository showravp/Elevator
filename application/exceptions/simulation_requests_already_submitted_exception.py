from application.exceptions.simulation_conflict_exception import SimulationConflictException


class SimulationRequestsAlreadySubmittedException(SimulationConflictException):
    """Requests are a one-shot batch per run, not a live stream — a run only ever
    transitions PENDING -> RUNNING once."""
