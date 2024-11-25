import socket

import serial

from src.domain.engine import Engine
from src.adapters.work.engine import SocketSessionFactory
from src.entrypoints.uart_test.monitor import MOCK_MONITOR_SOCKET_HOST, MOCK_MONITOR_SOCKET_PORT


def main():
    engine = Engine(
        session_factories=[
            SocketSessionFactory(
                server_socket=create_server_socket(),
                uart_client=create_uart(),
                monitor_socket=create_monitor_socket()
            )
        ]
    )
    engine.run()


def create_server_socket():
    server_socket = socket.create_server(('localhost', 6666), reuse_port=True)
    server_socket.settimeout(0)
    server_socket.listen()
    return server_socket


def create_uart():
    return serial.Serial(
        '/dev/ttyAMA0',
        baudrate=115200,
    )


def create_monitor_socket():
    return socket.create_connection((MOCK_MONITOR_SOCKET_HOST, MOCK_MONITOR_SOCKET_PORT))


if __name__ == "__main__":
    main()
