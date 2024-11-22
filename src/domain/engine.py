from __future__ import annotations

import abc
from typing import Iterable

from src.domain.exceptions import SessionIsClosed, PortException


class Session(abc.ABC):
    def run(self):
        while True:
            try:
                self.next()
            except SessionIsClosed:
                break

    @abc.abstractmethod
    def next(self):
        ...


class Port(abc.ABC):
    @abc.abstractmethod
    def create_session(self) -> Session:
        ...


class Engine:
    def __init__(self, ports: Iterable[Port]):
        self.ports = list(ports)
        assert self.ports, 'Ports cannot be empty'

    def run(self):
        while True:
            session = self.create_session()
            session.run()

    def create_session(self) -> Session:
        cursor = 0
        while True:
            port = self.ports[cursor % len(self.ports)]
            try:
                return port.create_session()
            except PortException:
                cursor += 1
