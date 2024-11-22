from src.domain.engine import Engine
from src.adapters.mock.engine import SocketPort


MOCK_SOCKET_HOST = 'localhost'
MOCK_SOCKET_PORT = 6666


def main():
    engine = Engine(
        ports=[
            SocketPort(
                host=MOCK_SOCKET_HOST,
                port=MOCK_SOCKET_PORT
            )
        ]
    )
    engine.run()


if __name__ == "__main__":
    main()
