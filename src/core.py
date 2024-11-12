from __future__ import annotations

import bisect
import abc
import dataclasses
import enum


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


class PlayerStateType(enum.Enum):
    PLAYING = 0
    PAUSED = 1
    NO_PLAYBACK = 2


class Player:
    def __init__(self, playback_factory: PlaybackFactory) -> None:
        self.playback_factory = playback_factory
        self.states: dict[PlayerStateType, PlayerState] = {
            PlayerStateType.PLAYING: PlayingState(player=self),
            PlayerStateType.PAUSED: PauseState(player=self),
            PlayerStateType.NO_PLAYBACK: NoPlaybackState(player=self),
        }
        self.state: PlayerState = self.states[PlayerStateType.NO_PLAYBACK]
        self.playback = None

    def load_playback(self, source: bytes) -> None:
        self.state.load_playback(source=source)

    def clear_playback(self) -> None:
        self.state.clear_playback()

    def play(self):
        self.state.play()

    def pause(self):
        self.state.pause()

    def stop(self):
        self.state.stop()

    def set_cursor(self, timestamp: int) -> None:
        self.state.set_cursor(timestamp=timestamp)

    def get_current_timestamp(self) -> int:
        return self.state.get_current_timestamp()

    def get_last_timestamp(self) -> int:
        return self.state.get_last_timestamp()

    def __iter__(self):
        return self

    def __next__(self):
        self.next()

    def next(self):
        self.state.next()


class PlayerState(abc.ABC):
    def __init__(self, player: Player):
        self.player = player

    @abc.abstractmethod
    def load_playback(self, source: bytes) -> None:
        ...

    @abc.abstractmethod
    def clear_playback(self) -> None:
        ...

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

    @abc.abstractmethod
    def next(self):
        ...


class PlayingState(PlayerState):
    def load_playback(self, source: bytes) -> None:
        self.player.playback_factory.create_playback(source=source)
        self.player.state = self.player.states[PlayerStateType.PAUSED]

    def clear_playback(self) -> None:
        self.player.playback = None
        self.player.state = self.player.states[PlayerStateType.NO_PLAYBACK]

    def play(self):
        self.player.playback.execute_action()

    def pause(self):
        self.player.state = self.player.states[PlayerStateType.PAUSED]

    def stop(self):
        self.player.playback.set_cursor(0)
        self.player.state = self.player.states[PlayerStateType.PAUSED]

    def set_cursor(self, timestamp: int) -> None:
        self.player.playback.set_cursor(timestamp=timestamp)

    def get_current_timestamp(self) -> int:
        return self.player.playback.get_current_timestamp()

    def get_last_timestamp(self) -> int:
        return self.player.playback.get_last_timestamp()

    def next(self):
        self.play()


class PauseState(PlayerState):
    def load_playback(self, source: bytes) -> None:
        self.player.playback_factory.create_playback(source=source)

    def clear_playback(self) -> None:
        self.player.playback = None
        self.player.state = self.player.states[PlayerStateType.NO_PLAYBACK]

    def play(self):
        pass

    def pause(self):
        pass

    def stop(self):
        self.player.playback.set_cursor(0)

    def set_cursor(self, timestamp: int) -> None:
        self.player.playback.set_cursor(timestamp=timestamp)

    def get_current_timestamp(self) -> int:
        return self.player.playback.get_current_timestamp()

    def get_last_timestamp(self) -> int:
        return self.player.playback.get_last_timestamp()


class NoPlaybackState(PlayerState):
    def load_playback(self, source: bytes) -> None:
        self.player.playback_factory.create_playback(source=source)
        self.player.state = self.player.states[PlayerStateType.PAUSED]

    def clear_playback(self) -> None:
        pass

    def play(self):
        pass

    def pause(self):
        pass

    def stop(self):
        self.player.playback.set_cursor(0)

    def set_cursor(self, timestamp: int) -> None:
        self.player.playback.set_cursor(timestamp=timestamp)

    def get_current_timestamp(self) -> int:
        return self.player.playback.get_current_timestamp()

    def get_last_timestamp(self) -> int:
        return self.player.playback.get_last_timestamp()

