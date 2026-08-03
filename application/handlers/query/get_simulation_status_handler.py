from application.ports import ISimulationRegistry
from application.queries import GetSimulationStatusQuery
from application.simulation_run import SimulationRun


class GetSimulationStatusHandler:
    def __init__(self, registry: ISimulationRegistry) -> None:
        self._registry = registry

    def handle(self, query: GetSimulationStatusQuery) -> SimulationRun:
        return self._registry.get(query.run_id)
