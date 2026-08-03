from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetPassengerStatsQuery:
    """No fields — same reasoning as GetPositionLogQuery."""
