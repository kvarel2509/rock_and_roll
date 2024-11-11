from __future__ import annotations

import bisect
import abc


class Action(abc.ABC):
    timestamp: int

    @abc.abstractmethod
    def execute(self):
        ...


class PlaybackIsFinished(Exception):
    pass


class Playback:
    def __init__(self, actions: list[Action]):
        self.actions = actions
        self.cursor = 0

    def execute_action(self):
        action = self.get_current_action()
        action.execute()
        self.cursor += 1

    def get_current_action(self) -> Action:
        try:
            return self.actions[self.cursor]
        except IndexError:
            raise PlaybackIsFinished()

    def get_current_timestamp(self) -> int:
        current_action = self.get_current_action()
        return current_action.timestamp

    def get_last_timestamp(self) -> int:
        last_action = self.actions[-1]
        return last_action.timestamp

    def set_cursor(self, timestamp: int) -> None:
        self.cursor = bisect.bisect_left(self.actions, timestamp, key=lambda action: action.timestamp)


class PlaybackFactory(abc.ABC):
    @abc.abstractmethod
    def create_playback(self, source: bytes) -> Playback:
        ...


class Player:
    def __init__(self, playback_factory: PlaybackFactory) -> None:
        self.playback_factory = playback_factory
        self.playback = None

    def load_playback(self, source: bytes) -> None:
        self.playback = self.playback_factory.create_playback(source=source)

    def clear_playback(self) -> None:
        self.playback = None

    @abc.abstractmethod
    def play(self):
        ...

    @abc.abstractmethod
    def pause(self):
        ...

    @abc.abstractmethod
    def stop(self):
        ...

    @abc.abstractmethod
    def set_cursor(self, timestamp: int) -> None:
        ...

    @abc.abstractmethod
    def get_current_timestamp(self) -> int:
        ...

    @abc.abstractmethod
    def get_last_timestamp(self) -> int:
        ...


class PlayerState(abc.ABC):
    def __init__(self, player: Player):
        self.player = player

    @abc.abstractmethod
    def play(self):
        ...

    @abc.abstractmethod
    def pause(self):
        ...

    @abc.abstractmethod
    def stop(self):
        ...

    @abc.abstractmethod
    def set_cursor(self, timestamp: int) -> None:
        ...

    @abc.abstractmethod
    def get_current_timestamp(self) -> int:
        ...

    @abc.abstractmethod
    def get_last_timestamp(self) -> int:
        ...
