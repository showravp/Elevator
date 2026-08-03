from application.projections import PassengerStatsProjection, PassengerStatsSummary
from application.queries import GetPassengerStatsQuery


class GetPassengerStatsHandler:
    def __init__(self, projection: PassengerStatsProjection) -> None:
        self._projection = projection

    def handle(self, query: GetPassengerStatsQuery) -> PassengerStatsSummary:
        return self._projection.summary()
