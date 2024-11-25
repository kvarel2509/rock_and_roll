import json
import select
import socket
from serial import Serial

from src.domain.engine import SessionFactory, Session
from src.domain.exceptions import SessionFactoryError, SessionIsClosed, CommandIsNotAvailable, InvalidCommand
from src.domain.player import Player
from .player import TextPlaybackBuilder


class SocketSession(Session):
    def __init__(self, client_socket: socket.socket, player: Player):
        self.client_socket = client_socket
        self.player = player

    def next(self):
        message = self.read_socket()
        if message is None:
            self.player.next()
        else:
            message = message.split(b':', maxsplit=1)
            try:
                if len(message) == 1:
                    [command_type] = message
                    if command_type == b'clear':
                        self.player.clear_playback()
                    elif command_type == b'play':
                        self.player.play()
                    elif command_type == b'pause':
                        self.player.pause()
                    elif command_type == b'stop':
                        self.player.stop()
                    else:
                        raise InvalidCommand()
                elif len(message) == 2:
                    command_type, payload = message
                    if command_type == b'load':
                        self.player.load_playback(source=payload)
                    elif command_type == b'cursor':
                        payload = int(payload)
                        self.player.set_cursor(timestamp=payload)
                    else:
                        raise InvalidCommand()
                else:
                    raise InvalidCommand()
            except CommandIsNotAvailable:
                response = {'type': 'COMMAND_NOT_AVAILABLE'}
                self.client_socket.sendall(json.dumps(response).encode())
            except InvalidCommand:
                response = {'type': 'INVALID_COMMAND'}
                self.client_socket.sendall(json.dumps(response).encode())
            except SessionIsClosed:
                self.client_socket.close()
                raise
            else:
                response = {'type': 'COMPLETED'}
                self.client_socket.sendall(json.dumps(response).encode())

    def read_socket(self):
        to_read, _, _ = select.select([self.client_socket], [], [], 0)
        if self.client_socket in to_read:
            message = self.client_socket.recv(4096)
            if message == b'':
                raise SessionIsClosed()
            return message


class SocketSessionFactory(SessionFactory):
    def __init__(self, server_socket: socket.socket, uart_client: Serial, monitor_socket: socket.socket):
        self.server_socket = server_socket
        self.uart_client = uart_client
        self.monitor_socket = monitor_socket

    def create_session(self) -> Session:
        try:
            client_socket, _ = self.server_socket.accept()
            return SocketSession(
                client_socket=client_socket,
                player=Player(
                    playback_factory=TextPlaybackBuilder(
                        uart_client=self.uart_client,
                        monitor_socket=self.monitor_socket
                    )
                )
            )
        except BlockingIOError:
            raise SessionFactoryError()
