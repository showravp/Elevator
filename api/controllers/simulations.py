from fastapi import APIRouter, BackgroundTasks, Depends

from api.run_scope import RunScope
from api.services import get_run_scope, get_simulation_registry, get_simulation_status_handler
from application.commands import ExecuteSimulationRunCommand
from application.exceptions import (
    SimulationConfigLockedException,
    SimulationRequestsAlreadySubmittedException,
)
from application.handlers.query import GetSimulationStatusHandler
from application.ports import ISimulationRegistry
from application.queries import (
    GetPassengerStatsQuery,
    GetPositionLogQuery,
    GetSimulationStatusQuery,
)
from application.raw_request import RawRequest
from application.simulation_config import SimulationConfig
from application.simulation_run_id import SimulationRunId
from application.simulation_status import SimulationStatus
from contracts import (
    PassengerStatsResponse,
    PositionLogResponse,
    PositionLogRowResponse,
    SimulationConfigBody,
    SimulationStatusResponse,
    SubmitRequestsBody,
)
from domain.value_objects import Floor, PassengerId, Tick

router = APIRouter(prefix="/simulations", tags=["simulations"])


def _to_config(body: SimulationConfigBody) -> SimulationConfig:
    return SimulationConfig(
        num_elevators=body.num_elevators,
        num_floors=body.num_floors,
        elevator_capacity=body.elevator_capacity,
    )


@router.post("", response_model=SimulationStatusResponse, status_code=201)
def create_simulation(
    body: SimulationConfigBody,
    registry: ISimulationRegistry = Depends(get_simulation_registry),
    run_scope: RunScope = Depends(get_run_scope),
) -> SimulationStatusResponse:
    run_id = run_scope.create_run(_to_config(body))
    run = registry.get(run_id)
    return SimulationStatusResponse(id=run.id.value, status=run.status.value)


@router.put("/{run_id}/config", response_model=SimulationStatusResponse)
def update_config(
    run_id: str,
    body: SimulationConfigBody,
    registry: ISimulationRegistry = Depends(get_simulation_registry),
    run_scope: RunScope = Depends(get_run_scope),
) -> SimulationStatusResponse:
    parsed_id = SimulationRunId(run_id)
    run = registry.get(parsed_id)
    if run.status is not SimulationStatus.PENDING:
        raise SimulationConfigLockedException(
            f"simulation run {run_id} already has requests submitted "
            f"(status={run.status.value}) — config can no longer be changed"
        )
    run_scope.update_config(parsed_id, _to_config(body))
    return SimulationStatusResponse(id=run.id.value, status=run.status.value)


@router.post("/{run_id}/requests", response_model=SimulationStatusResponse, status_code=202)
def submit_requests(
    run_id: str,
    body: SubmitRequestsBody,
    background_tasks: BackgroundTasks,
    registry: ISimulationRegistry = Depends(get_simulation_registry),
    run_scope: RunScope = Depends(get_run_scope),
) -> SimulationStatusResponse:
    parsed_id = SimulationRunId(run_id)
    run = registry.get(parsed_id)
    if run.status is not SimulationStatus.PENDING:
        raise SimulationRequestsAlreadySubmittedException(
            f"simulation run {run_id} already has requests submitted (status={run.status.value})"
        )
    raw_requests = [
        RawRequest(
            passenger_id=PassengerId(item.id),
            source=Floor(item.source),
            destination=Floor(item.dest),
            tick=Tick(item.time),
        )
        for item in body.requests
    ]
    container = run_scope.attach_requests(parsed_id, raw_requests)
    # Set synchronously, before scheduling the background task, so a request racing this
    # one sees RUNNING immediately rather than a narrow window where status still reads
    # PENDING despite requests already having been accepted.
    run.status = SimulationStatus.RUNNING
    background_tasks.add_task(
        container.execute_run_handler().handle, ExecuteSimulationRunCommand(parsed_id)
    )
    return SimulationStatusResponse(id=run.id.value, status=run.status.value)


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
    if run.status is SimulationStatus.PENDING:
        # Confirmed to exist (registry.get() above would have raised otherwise), just no
        # requests submitted yet — nothing to report rather than a misleading 404.
        return PositionLogResponse(status=run.status.value, rows=[])
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
    if run.status is SimulationStatus.PENDING:
        return PassengerStatsResponse(
            status=run.status.value,
            completed_count=0,
            still_in_progress_count=0,
            min_wait_time=0,
            max_wait_time=0,
            avg_wait_time=0.0,
            min_total_time=0,
            max_total_time=0,
            avg_total_time=0.0,
        )
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
