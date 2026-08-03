from application.queries import GetPassengerStatsQuery
from application.read_models import PassengerStatsSummary
from application.repositories import PassengerStatsRepository


class GetPassengerStatsHandler:
    def __init__(self, repository: PassengerStatsRepository) -> None:
        self._repository = repository

    def handle(self, query: GetPassengerStatsQuery) -> PassengerStatsSummary:
        return self._repository.get_summary()
