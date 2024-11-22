from __future__ import annotations


class SessionIsClosed(Exception):
    pass


class PortException(Exception):
    pass


class PlaybackIsFinished(Exception):
    pass
