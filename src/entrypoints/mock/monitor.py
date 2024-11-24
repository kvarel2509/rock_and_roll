import json
import socket

MOCK_MONITOR_SOCKET_HOST = 'localhost'
MOCK_MONITOR_SOCKET_PORT = 6667


def main():
    server_socket = socket.create_server((MOCK_MONITOR_SOCKET_HOST, MOCK_MONITOR_SOCKET_PORT))
    while True:
        monitor_socket, _ = server_socket.accept()
        print(_)
        with monitor_socket:
            while True:
                body = monitor_socket.recv(4096)
                if not body:
                    break
                print(body.decode())


if __name__ == "__main__":
    main()