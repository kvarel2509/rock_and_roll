from __future__ import annotations
import abc


class Observer(abc.ABC):
    @abc.abstractmethod
    def update(self, observable: Observable) -> None:
        ...


class Observable(abc.ABC):
    @abc.abstractmethod
    def add_observer(self, observer: Observer) -> None:
        ...

    @abc.abstractmethod
    def remove_observer(self, observer: Observer) -> None:
        ...

    @abc.abstractmethod
    def notify_observers(self) -> None:
        ...
