from fastapi import Request

from application.handlers.query import GetSimulationStatusHandler
from application.ports import SimulationRegistry
from composition.run_scope import RunScope


def get_run_scope(request: Request) -> RunScope:
    return request.app.state.run_scope


def get_simulation_registry(request: Request) -> SimulationRegistry:
    return request.app.state.simulation_registry


def get_simulation_status_handler(request: Request) -> GetSimulationStatusHandler:
    return GetSimulationStatusHandler(request.app.state.simulation_registry)
