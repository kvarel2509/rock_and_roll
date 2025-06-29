import socket

from src.entrypoints.socket.server import MOCK_SOCKET_HOST, MOCK_SOCKET_PORT


def main():
    client_socket = socket.create_connection((MOCK_SOCKET_HOST, MOCK_SOCKET_PORT))
    with client_socket:
        while True:
            command = input('Введите команду: ')
            if command:
                client_socket.sendall(command.encode())


if __name__ == '__main__':
    main()
