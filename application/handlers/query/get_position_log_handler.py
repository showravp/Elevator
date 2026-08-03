from application.queries import GetPositionLogQuery
from application.read_models import PositionLogRow
from application.repositories import PositionLogRepository


class GetPositionLogHandler:
    def __init__(self, repository: PositionLogRepository) -> None:
        self._repository = repository

    def handle(self, query: GetPositionLogQuery) -> list[PositionLogRow]:
        return self._repository.get_rows()
