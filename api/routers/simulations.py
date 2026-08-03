from fastapi import APIRouter, BackgroundTasks, Depends

from api.dependencies import get_run_scope, get_simulation_registry, get_simulation_status_handler
from api.schemas import (
    CreateSimulationRequestBody,
    PassengerStatsResponse,
    PositionLogResponse,
    PositionLogRowResponse,
    SimulationStatusResponse,
)
from application.commands import ExecuteSimulationRunCommand
from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry
from application.queries import (
    GetPassengerStatsQuery,
    GetPositionLogQuery,
    GetSimulationStatusQuery,
)
from application.raw_request import RawRequest
from application.simulation_run_id import SimulationRunId
from composition.run_scope import RunScope
from domain.value_objects import Floor, PassengerId, Tick

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationStatusResponse, status_code=202)
def create_simulation(
    body: CreateSimulationRequestBody,
    background_tasks: BackgroundTasks,
    run_scope: RunScope = Depends(get_run_scope),
) -> SimulationStatusResponse:
    raw_requests = [
        RawRequest(
            passenger_id=PassengerId(item.id),
            source=Floor(item.source),
            destination=Floor(item.dest),
            tick=Tick(item.time),
        )
        for item in body.requests
    ]
    run_id = run_scope.create(
        requests=raw_requests,
        num_elevators=body.num_elevators,
        num_floors=body.num_floors,
        elevator_capacity=body.elevator_capacity,
    )
    container = run_scope.get_container(run_id)
    background_tasks.add_task(
        container.execute_run_handler().handle, ExecuteSimulationRunCommand(run_id)
    )
    return SimulationStatusResponse(id=run_id.value, status="pending")


@router.get("/{run_id}", response_model=SimulationStatusResponse)
def get_status(
    run_id: str,
    handler: GetSimulationStatusHandler = Depends(get_simulation_status_handler),
) -> SimulationStatusResponse:
    run = handler.handle(GetSimulationStatusQuery(SimulationRunId(run_id)))
    return SimulationStatusResponse(
        id=run.id.value, status=run.status.value, error_message=run.error_message
    )


@router.get("/{run_id}/position-log", response_model=PositionLogResponse)
def get_position_log(
    run_id: str,
    run_scope: RunScope = Depends(get_run_scope),
    registry: ISimulationRegistry = Depends(get_simulation_registry),
) -> PositionLogResponse:
    parsed_id = SimulationRunId(run_id)
    run = registry.get(parsed_id)
    container = run_scope.get_container(parsed_id)
    rows = container.position_log_query_handler().handle(GetPositionLogQuery())
    return PositionLogResponse(
        status=run.status.value,
        rows=[
            PositionLogRowResponse(
                tick=row.tick.value, elevator_id=row.elevator_id.value, floor=row.floor.value
            )
            for row in rows
        ],
    )


@router.get("/{run_id}/passenger-stats", response_model=PassengerStatsResponse)
def get_passenger_stats(
    run_id: str,
    run_scope: RunScope = Depends(get_run_scope),
    registry: ISimulationRegistry = Depends(get_simulation_registry),
) -> PassengerStatsResponse:
    parsed_id = SimulationRunId(run_id)
    run = registry.get(parsed_id)
    container = run_scope.get_container(parsed_id)
    summary = container.passenger_stats_query_handler().handle(GetPassengerStatsQuery())
    return PassengerStatsResponse(
        status=run.status.value,
        completed_count=summary.completed_count,
        still_in_progress_count=summary.still_in_progress_count,
        min_wait_time=summary.min_wait_time,
        max_wait_time=summary.max_wait_time,
        avg_wait_time=summary.avg_wait_time,
        min_total_time=summary.min_total_time,
        max_total_time=summary.max_total_time,
        avg_total_time=summary.avg_total_time,
    )
