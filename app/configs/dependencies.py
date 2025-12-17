from fastapi import Depends
from typing import Type, TypeVar, Callable

# Type variables for generic repo and service
R = TypeVar("R")
S = TypeVar("S")

def get_repository(repo_cls: Type[R]) -> Callable[[], R]:
    """Factory to create repository dependency."""
    def _get_repo() ->R:
        return repo_cls()
    return _get_repo

def get_service_factory(service_cls: Type[S], repo_cls: Type[R]) -> Callable[[R],S]:
    """Factory to create service dependency with repository injected."""
    repo_dependency = get_repository(repo_cls)

    def _get_service(repo: R = Depends(repo_dependency))-> S:
        return service_cls(repo)
    return _get_service
