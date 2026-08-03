from application.exceptions.application_exception import ApplicationException


class SimulationConflictException(ApplicationException):
    """Base for "the run is in a state that doesn't allow this operation" — maps to
    HTTP 409. Subclassed rather than reused directly so each concrete situation
    (config locked, requests already submitted) stays precisely named."""
