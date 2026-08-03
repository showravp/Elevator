from application.exceptions.simulation_conflict_exception import SimulationConflictException


class SimulationConfigLockedException(SimulationConflictException):
    """Config is only mutable while the run is still PENDING — once requests have been
    submitted, changing config would silently orphan whatever already ran against the
    old one."""
