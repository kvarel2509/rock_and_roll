import json
import socket
import time

import serial

from src.domain.player import Action, Playback, PlaybackFactory
from src.generic.observer import Observer


class UARTSendAction(Action):
    FINISH_MARKER = b'\n'

    def __init__(self, uart_client: serial.Serial, timestamp: int, payload: bytes):
        self.uart_client = uart_client
        self.timestamp = timestamp
        self.payload = payload

    def get_timestamp(self) -> int:
        return self.timestamp

    def execute(self):
        print(f'Sending {self.payload}')
        self.uart_client.write(self.payload + self.FINISH_MARKER)


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


class TextPlaybackBuilder(PlaybackFactory):
    def __init__(self, uart_client: serial.Serial, monitor_socket: socket.socket):
        self.uart_client = uart_client
        self.monitor_socket = monitor_socket

    def create_playback(self, payload: bytes) -> Playback:
        active_commands = []
        for command in payload.strip(b'#').split(b'#'):
            timestamp, command = command.split(b'.', maxsplit=1)
            action = UARTSendAction(
                uart_client=self.uart_client,
                timestamp=int(timestamp),
                payload=command
            )
            active_commands.append(action)
        actions = []
        cursor = 0
        for active_command in sorted(active_commands, key=lambda x: x.get_timestamp()):
            command_timestamp = active_command.get_timestamp()
            silence_duration = command_timestamp - cursor
            if silence_duration:
                silence_action = SilenceAction(
                    timestamp=cursor,
                    ms=silence_duration
                )
                actions.append(silence_action)
            actions.append(active_command)
            cursor = command_timestamp
        playback = Playback(actions=actions)
        playback.add_observer(
            observer=TimelineNotifyObserver(
                client_socket=self.monitor_socket
            )
        )
        return playback
