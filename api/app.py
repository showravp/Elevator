from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.bootstrap import bootstrap_api_state
from api.routers.simulations import router as simulations_router
from application.exceptions import SimulationConflictException, SimulationRunNotFoundException


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
