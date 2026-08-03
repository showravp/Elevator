from application.queries import GetPassengerStatsQuery
from application.read_models import PassengerStatsSummary
from application.repositories import IPassengerStatsRepository


class GetPassengerStatsHandler:
    def __init__(self, repository: IPassengerStatsRepository) -> None:
        self._repository = repository

    def handle(self, query: GetPassengerStatsQuery) -> PassengerStatsSummary:
        return self._repository.get_summary()
