from Server import Server
import socket


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 8765))
    server_socket.listen()
    server_socket.setblocking(False)
    Server(server_socket).run()


if __name__ == "__main__":
    main()
