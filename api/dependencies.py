from fastapi import Request

from api.run_scope import RunScope
from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry


def get_run_scope(request: Request) -> RunScope:
    return request.app.state.run_scope


def get_simulation_registry(request: Request) -> ISimulationRegistry:
    return request.app.state.simulation_registry


def get_simulation_status_handler(request: Request) -> GetSimulationStatusHandler:
    return request.app.state.simulation_status_handler
