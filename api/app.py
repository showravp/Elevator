from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers.simulations import router as simulations_router
from application.exceptions import SimulationRunNotFoundException
from composition.api_bootstrap import bootstrap_api_state


def create_app(output_dir: Path = Path("output")) -> FastAPI:
    app = FastAPI(title="Elevator Simulation API")

    registry, run_scope, status_handler = bootstrap_api_state(output_dir=output_dir)
    app.state.simulation_registry = registry
    app.state.run_scope = run_scope
    app.state.simulation_status_handler = status_handler

    app.include_router(simulations_router)

    @app.exception_handler(SimulationRunNotFoundException)
    def handle_not_found(request: Request, exc: SimulationRunNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


app = create_app()
