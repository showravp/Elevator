from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.controllers.simulations import router as simulations_router
from api.run_scope import RunScope
from application.exceptions import SimulationConflictException, SimulationRunNotFoundException
from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry
from infrastructure.csv_config_repository import CsvConfigRepository
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def bootstrap_api_state(
    output_dir: Path = Path("output"),
) -> tuple[ISimulationRegistry, RunScope, GetSimulationStatusHandler]:
    """Process-wide state for the life of the server: one registry, one RunScope, one
    status query handler. This — together with api/program.py's build_application() — is
    where infrastructure concrete classes get constructed for the API; controllers never
    do, same rule as everywhere else in the app, just enforced by file boundary within
    api/ rather than by a separate composition/ package. api/controllers/ only ever
    receives already-built instances via app.state, never builds its own."""
    registry = InMemorySimulationRegistry()
    config_repository = CsvConfigRepository(output_dir=output_dir)
    run_scope = RunScope(registry, config_repository, output_dir=output_dir)
    status_handler = GetSimulationStatusHandler(registry)
    return registry, run_scope, status_handler


def _handle_not_found(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


def _handle_conflict(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


def create_app(output_dir: Path = Path("output")) -> FastAPI:
    app = FastAPI(title="Elevator Simulation API")

    registry, run_scope, status_handler = bootstrap_api_state(output_dir=output_dir)
    app.state.simulation_registry = registry
    app.state.run_scope = run_scope
    app.state.simulation_status_handler = status_handler

    app.include_router(simulations_router)
    # add_exception_handler() rather than the @app.exception_handler(...) decorator form —
    # the decorator registers the function as a side effect that static analysis can't see
    # as a "use", so it reads as dead code under strict checking. This explicit call form
    # is equally idiomatic FastAPI and makes the registration visible to the type checker.
    app.add_exception_handler(SimulationRunNotFoundException, _handle_not_found)
    # Registered on the base class — catches SimulationConfigLockedException and
    # SimulationRequestsAlreadySubmittedException (and any future conflict subclass)
    # without needing a handler per concrete exception.
    app.add_exception_handler(SimulationConflictException, _handle_conflict)

    return app


app = create_app()
