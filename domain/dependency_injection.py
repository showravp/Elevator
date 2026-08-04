from dependency_injector import containers, providers

from domain.services.strategies import NearestCarSchedulingPolicy


class DomainServicesContainer(containers.DeclarativeContainer):
    scheduling_policy = providers.Singleton(NearestCarSchedulingPolicy)
