from Server import Server
import socket


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 8765))
    server_socket.listen()
    server_socket.setblocking(False)
    audio_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    audio_server.bind(("localhost", 8766))
    audio_server.setblocking(False)
    Server(server_socket, audio_server).run()


if __name__ == "__main__":
    main()
