import dataclasses
import json
import socket
import time

from src.domain.player import Action, Playback, PlaybackFactory
from src.generic.observer import Observer


class PrintAction(Action):
    def __init__(self, timestamp, text):
        self.timestamp = timestamp
        self.text = text

    def get_timestamp(self) -> int:
        return self.timestamp

    def execute(self):
        print(self.text)


class KaraokeTextPrintAction(Action):
    def __init__(self, client_socket: socket.socket, timestamp: int, text: str):
        self.client_socket = client_socket
        self.timestamp = timestamp
        self.text = text

    def get_timestamp(self) -> int:
        return self.timestamp

    def execute(self):
        body = {'type': 'KARAOKE', 'text': self.text}
        self.client_socket.sendall(json.dumps(body).encode())


class SilenceAction(Action):
    def __init__(self, timestamp, ms: int):
        self.timestamp = timestamp
        self.ms = ms

    def get_timestamp(self) -> int:
        return self.timestamp

    def execute(self):
        time.sleep(self.ms / 1000)


class TimelineNotifyObserver(Observer):
    def __init__(self, client_socket: socket.socket):
        self.client_socket = client_socket
        self.prev_timestamp = None

    def update(self, observable: Playback):
        current_timestamp = observable.get_current_timestamp()
        if current_timestamp != self.prev_timestamp:
            self.notify(timestamp=current_timestamp)
            self.prev_timestamp = current_timestamp

    def notify(self, timestamp: int):
        notification = {
            'type': 'TIMELINE_CHANGED',
            'payload': {
                'current_timestamp': timestamp,
            }
        }
        self.client_socket.send(json.dumps(notification).encode())


@dataclasses.dataclass
class ActionTimeline:
    start: int
    duration: int
    action: Action


class TextPlaybackBuilder(PlaybackFactory):
    def __init__(self, monitor_socket: socket.socket):
        self.monitor_socket = monitor_socket

    def create_playback(self, payload: bytes) -> Playback:
        action_timelines = []
        actions = []
        cursor = 0
        for command in payload.split(b'&'):
            timestamp, command_type, command = command.split(b':', maxsplit=2)
            if command_type == b'':
                action = PrintAction(
                    timestamp=int(timestamp),
                    text=str(command)
                )
            else:
                action = KaraokeTextPrintAction(
                    client_socket=self.monitor_socket,
                    timestamp=int(timestamp),
                    text=str(command)
                )
            action_timeline = ActionTimeline(
                start=int(timestamp),
                duration=0,
                action=action
            )
            action_timelines.append(action_timeline)

        for action_timeline in sorted(action_timelines, key=lambda x: x.start):
            start = action_timeline.start
            silence_duration = start - cursor
            if silence_duration:
                silence_action = SilenceAction(
                    timestamp=cursor,
                    ms=silence_duration
                )
                actions.append(silence_action)
            actions.append(action_timeline.action)
            cursor = start + action_timeline.duration
        playback = Playback(actions=actions)
        playback.add_observer(observer=TimelineNotifyObserver(client_socket=self.monitor_socket))
        return playback
