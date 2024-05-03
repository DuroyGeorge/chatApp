import socket
import json
import struct
from Format import Format


def client():
    host = "localhost"
    port = 8765

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        response = s.recv(4)
        response = int.from_bytes(response, "big")
        print("> recv:", response)
        response = s.recv(response).decode()
        print("> recv:", response)

        # 获取用户名和密码
        username = input("Username: ")
        password = input("Password: ")

        # 准备发送的消息
        message = json.dumps({"code": 0, "username": username, "password": password})
        print("> Sent:", message)
        s.sendall(
            Format({"code": 0, "username": username, "password": password}).toBytes()
        )


client()
