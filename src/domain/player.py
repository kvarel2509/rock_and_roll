from __future__ import annotations

import abc
import bisect
import enum

from src.domain.exceptions import PlaybackIsFinished, CommandIsNotAvailable
from src.generic.observer import Observable, Observer


class Action(abc.ABC):
    @abc.abstractmethod
    def get_timestamp(self) -> int:
        ...

    @abc.abstractmethod
    def execute(self):
        ...


class Playback(Observable, abc.ABC):
    def __init__(self, actions: list[Action]):
        self.actions = actions
        self.cursor = 0
        self.observers = set()

    def execute_action(self):
        action = self.get_current_action()
        action.execute()
        self.cursor += 1
        self.notify_observers()

    def get_current_action(self) -> Action:
        try:
            return self.actions[self.cursor]
        except IndexError:
            raise PlaybackIsFinished()

    def set_cursor(self, timestamp: int):
        self.cursor = bisect.bisect_left(self.actions, timestamp, key=lambda action: action.get_timestamp())
        self.notify_observers()

    def get_current_timestamp(self) -> int:
        current_action = self.get_current_action()
        return current_action.get_timestamp()

    def get_last_timestamp(self) -> int:
        last_action = self.actions[-1]
        return last_action.get_timestamp()

    def add_observer(self, observer: Observer) -> None:
        self.observers.add(observer)

    def remove_observer(self, observer: Observer) -> None:
        self.observers.discard(observer)

    def notify_observers(self) -> None:
        for observer in self.observers:
            observer.update(observable=self)


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

    def load_playback(self, source: bytes):
        raise CommandIsNotAvailable()

    def clear_playback(self):
        raise CommandIsNotAvailable()

    def play(self):
        raise CommandIsNotAvailable()

    def pause(self):
        raise CommandIsNotAvailable()

    def stop(self):
        raise CommandIsNotAvailable()

    def set_cursor(self, timestamp: int):
        raise CommandIsNotAvailable()

    @abc.abstractmethod
    def next(self):
        ...


class PlayingState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)

    def clear_playback(self):
        self.player.playback = None
        self.player.set_state(state_type=PlayerStateType.NO_PLAYBACK)

    def play(self):
        self.next()

    def pause(self):
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def stop(self):
        self.player.playback.set_cursor(0)
        self.player.set_state(state_type=PlayerStateType.PAUSED)

    def set_cursor(self, timestamp: int):
        self.player.playback.set_cursor(timestamp=timestamp)

    def next(self):
        try:
            self.player.playback.execute_action()
        except PlaybackIsFinished:
            self.player.playback.set_cursor(0)
            self.player.set_state(state_type=PlayerStateType.PAUSED)


class PauseState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)
        self.player.set_state(state_type=PlayerStateType.PLAYING)

    def clear_playback(self):
        self.player.playback = None
        self.player.set_state(state_type=PlayerStateType.NO_PLAYBACK)

    def play(self):
        self.player.set_state(state_type=PlayerStateType.PLAYING)

    def pause(self):
        self.next()

    def stop(self):
        self.player.playback.set_cursor(0)

    def set_cursor(self, timestamp: int):
        self.player.playback.set_cursor(timestamp=timestamp)

    def next(self):
        pass


class NoPlaybackState(PlayerState):
    def load_playback(self, source: bytes):
        self.player.playback = self.player.playback_factory.create_playback(payload=source)
        self.player.set_state(state_type=PlayerStateType.PLAYING)

    def next(self):
        pass
