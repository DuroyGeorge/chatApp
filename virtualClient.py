import socket
import json


def client():
    host = "127.0.0.1"
    port = 8765

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        response = s.recv(1024).decode()
        print("> recv:", response)

        # 获取用户名和密码
        username = input("Username: ")
        password = input("Password: ")

        # 准备发送的消息
        message = json.dumps({"code": 0, "username": username, "password": password})
        s.sendall(message.encode())

        print("> Sent:", message)

        # 等待并接收响应
        response = s.recv(1024).decode()
        print("> recv:", response)


client()
