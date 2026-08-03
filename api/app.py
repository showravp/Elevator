from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers.simulations import router as simulations_router
from application.exceptions import SimulationRunNotFoundError
from composition.run_scope import RunScope
from infrastructure.in_memory_simulation_registry import InMemorySimulationRegistry


def create_app() -> FastAPI:
    app = FastAPI(title="Elevator Simulation API")

    registry = InMemorySimulationRegistry()
    app.state.simulation_registry = registry
    app.state.run_scope = RunScope(registry)

    app.include_router(simulations_router)

    @app.exception_handler(SimulationRunNotFoundError)
    def handle_not_found(request: Request, exc: SimulationRunNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


app = create_app()
