import contextlib
import select
import socket
import time

from src.domain.engine import Port, Session
from src.domain.exceptions import PortException, SessionIsClosed
from src.domain.player import Player
from .player import TextPlaybackBuilder


class SocketSession(Session):
    def __init__(self, client_socket: socket.socket, player: Player):
        self.client_socket = client_socket
        self.player = player

    def next(self):
        to_read, _, _ = select.select([self.client_socket], [], [], 0)
        if self.client_socket in to_read:
            body = self.client_socket.recv(4096).split(b':', maxsplit=1)
            if len(body) == 1:
                [command_type] = body
                if command_type is b'':
                    self.client_socket.close()
                    raise SessionIsClosed()
                if command_type == b'clear':
                    return self.player.clear_playback()
                elif command_type == b'play':
                    return self.player.play()
                elif command_type == b'pause':
                    return self.player.pause()
                elif command_type == b'stop':
                    return self.player.stop()
            elif len(body) == 2:
                command_type, payload = body
                if command_type == b'load':
                    print('111111')
                    return self.player.load_playback(source=payload)
                elif command_type == b'cursor':
                    with contextlib.suppress(ValueError):
                        payload = int(payload)
                        return self.player.set_cursor(timestamp=payload)
        return self.player.next()


class SocketPort(Port):
    def __init__(self, host: str, port: int):
        self.server_socket = socket.create_server((host, port), reuse_port=True)
        self.server_socket.settimeout(0)
        self.server_socket.listen()

    def create_session(self) -> Session:
        try:
            client_socket, _ = self.server_socket.accept()
            print('Подключено', _)
            return SocketSession(
                client_socket=client_socket,
                player=self.create_player()
            )
        except BlockingIOError:
            raise PortException()

    def create_player(self) -> Player:
        return Player(
            playback_factory=TextPlaybackBuilder()
        )
