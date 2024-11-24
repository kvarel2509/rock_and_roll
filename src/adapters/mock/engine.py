import json
import select
import socket

from src.domain.engine import Port, Session
from src.domain.exceptions import PortException, SessionIsClosed, CommandIsNotAvailable, InvalidCommand
from src.domain.player import Player
from .player import TextPlaybackBuilder
from ...entrypoints.mock.monitor import MOCK_MONITOR_SOCKET_HOST, MOCK_MONITOR_SOCKET_PORT


class SocketSession(Session):
    def __init__(self, client_socket: socket.socket, player: Player):
        self.client_socket = client_socket
        self.player = player

    def next(self):
        to_read, _, _ = select.select([self.client_socket], [], [], 0)
        if self.client_socket in to_read:
            body = self.client_socket.recv(4096).split(b':', maxsplit=1)
            try:
                if len(body) == 1:
                    [command_type] = body
                    if command_type is b'':
                        self.client_socket.close()
                        raise SessionIsClosed()
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
                elif len(body) == 2:
                    command_type, payload = body
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
            else:
                response = {'type': 'COMPLETED'}
                self.client_socket.sendall(json.dumps(response).encode())
        self.player.next()


class SocketPort(Port):
    def __init__(self, host: str, port: int):
        self.server_socket = socket.create_server((host, port), reuse_port=True)
        self.server_socket.settimeout(0)
        self.server_socket.listen()

    def create_session(self) -> Session:
        try:
            client_socket, _ = self.server_socket.accept()
            monitor_socket = socket.create_connection((MOCK_MONITOR_SOCKET_HOST, MOCK_MONITOR_SOCKET_PORT))
            print('Подключено', _)
            return SocketSession(
                client_socket=client_socket,
                player=Player(
                    playback_factory=TextPlaybackBuilder(
                        control_socket=client_socket,
                        monitor_socket=monitor_socket
                    )
                )
            )
        except BlockingIOError:
            raise PortException()
