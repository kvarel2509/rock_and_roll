from __future__ import annotations

import abc
import bisect
import enum

from src.domain.exceptions import PlaybackIsFinished


class Action(abc.ABC):
    timestamp: int

    @abc.abstractmethod
    def execute(self):
        ...


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

    def set_cursor(self, timestamp: int):
        self.cursor = bisect.bisect_left(self.actions, timestamp, key=lambda action: action.timestamp)


class PlaybackFactory:
    def create_playback(self, payload: bytes) -> Playback:
        ...


class PlaybackBuilder(abc.ABC):
    """
    Может быть востребован, когда необходимо собирать трек и отчитываться о
    сборке или дать возможность прекратить сборку в любой момент.
    Использовать его сможет например состояние плейера
    """

    @abc.abstractmethod
    def start_build(self, payload: bytes):
        ...

    @abc.abstractmethod
    def next(self):
        ...

    @abc.abstractmethod
    def create_playback(self) -> Playback:
        ...


class PlayerStateType(enum.Enum):
    PLAYING = 0
    PAUSED = 1
    NO_PLAYBACK = 2


class Player:
    def __init__(self, playback_factory: PlaybackFactory):
        self.playback_factory = playback_factory
        self.states: dict[PlayerStateType, PlayerState] = {
            PlayerStateType.PLAYING: PlayingState(player=self),
            PlayerStateType.PAUSED: PauseState(player=self),
            PlayerStateType.NO_PLAYBACK: NoPlaybackState(player=self)
        }
        self.state: PlayerState = self.states[PlayerStateType.NO_PLAYBACK]
        self.playback = None

    def load_playback(self, source: bytes):
        self.state.load_playback(source=source)

    def clear_playback(self):
        self.state.clear_playback()

    def play(self):
        self.state.play()

    def pause(self):
        self.state.pause()

    def stop(self):
        self.state.stop()

    def set_cursor(self, timestamp: int):
        self.state.set_cursor(timestamp=timestamp)

    def set_state(self, state_type: PlayerStateType):
        self.state = self.states[state_type]

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
    def load_playback(self, source: bytes):
        ...

    @abc.abstractmethod
    def clear_playback(self):
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
    def set_cursor(self, timestamp: int):
        ...

    @abc.abstractmethod
    def next(self):
        ...


class PlayingState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def clear_playback(self):
        self.player.playback = None
        self.player.set_state(state_type=PlayerStateType.NO_PLAYBACK)

    def play(self):
        try:
            self.player.playback.execute_action()
        except PlaybackIsFinished:
            self.player.playback.set_cursor(0)
            self.player.set_state(state_type=PlayerStateType.PAUSED)

    def pause(self):
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def stop(self):
        self.player.playback.set_cursor(0)
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def set_cursor(self, timestamp: int):
        self.player.playback.set_cursor(timestamp=timestamp)

    def next(self):
        self.play()


class PauseState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)

    def clear_playback(self):
        self.player.playback = None
        self.player.set_state(state_type=PlayerStateType.NO_PLAYBACK)

    def play(self):
        self.player.set_state(state_type=PlayerStateType.PLAYING)

    def pause(self):
        pass

    def stop(self):
        self.player.playback.set_cursor(0)

    def set_cursor(self, timestamp: int):
        self.player.playback.set_cursor(timestamp=timestamp)

    def next(self):
        self.pause()


class NoPlaybackState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def clear_playback(self):
        pass

    def play(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def set_cursor(self, timestamp: int):
        pass

    def next(self):
        pass
