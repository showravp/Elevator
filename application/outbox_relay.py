from application.ports import IEventBus, IOutboxStore


class OutboxRelay:
    def __init__(self, outbox_store: IOutboxStore, event_bus: IEventBus) -> None:
        self._outbox_store = outbox_store
        self._event_bus = event_bus

    def drain(self) -> None:
        entries = self._outbox_store.pending()
        for entry in entries:
            self._event_bus.publish(entry.event)
        self._outbox_store.mark_dispatched([entry.sequence for entry in entries])
