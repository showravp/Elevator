from dataclasses import dataclass

from domain.events.domain_event import DomainEvent
from domain.value_objects import Floor, PassengerId, Tick


@dataclass(frozen=True, slots=True)
class RequestSubmitted(DomainEvent):
    passenger_id: PassengerId
    source: Floor
    destination: Floor
    tick: Tick
