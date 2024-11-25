from __future__ import annotations

import abc
from typing import Iterable

from src.domain.exceptions import SessionIsClosed, SessionFactoryError


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


class SessionFactory(abc.ABC):
    @abc.abstractmethod
    def create_session(self) -> Session:
        ...


class Engine:
    def __init__(self, session_factories: Iterable[SessionFactory]):
        self.session_factories = list(session_factories)
        assert self.session_factories, 'session_factories cannot be empty'

    def run(self):
        while True:
            session = self.create_session()
            session.run()

    def create_session(self) -> Session:
        cursor = 0
        while True:
            session_factory = self.session_factories[cursor % len(self.session_factories)]
            try:
                return session_factory.create_session()
            except SessionFactoryError:
                cursor += 1
