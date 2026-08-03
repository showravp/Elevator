from application.projections import PositionLogProjection, PositionLogRow
from application.queries import GetPositionLogQuery


class GetPositionLogHandler:
    def __init__(self, projection: PositionLogProjection) -> None:
        self._projection = projection

    def handle(self, query: GetPositionLogQuery) -> list[PositionLogRow]:
        return self._projection.rows
