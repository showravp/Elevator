from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetPositionLogQuery:
    """No fields: the query is already scoped to one run's projections by container
    selection, which happens one layer up (composition), not here."""
