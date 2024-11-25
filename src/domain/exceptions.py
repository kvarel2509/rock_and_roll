from __future__ import annotations


class SessionIsClosed(Exception):
    pass


class InvalidCommand(Exception):
    pass


class CommandIsNotAvailable(Exception):
    pass


class SessionFactoryError(Exception):
    pass


class PlaybackIsFinished(Exception):
    pass
