from dataclasses import dataclass

from domain.value_objects import Floor, PassengerId, Tick


@dataclass(frozen=True, slots=True)
class RawRequest:
    passenger_id: PassengerId
    source: Floor
    destination: Floor
    tick: Tick
