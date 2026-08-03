from application.ports import SimulationRegistry
from application.queries import GetSimulationStatusQuery
from application.simulation_run import SimulationRun


class GetSimulationStatusHandler:
    def __init__(self, registry: SimulationRegistry) -> None:
        self._registry = registry

    def handle(self, query: GetSimulationStatusQuery) -> SimulationRun:
        return self._registry.get(query.run_id)
