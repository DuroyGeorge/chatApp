import json
from concurrent.futures import ThreadPoolExecutor
import asyncio


class Server:

    def __init__(self, server_socket) -> None:
        self.connected = set()
        self.activeUser = {}
        self.server_socket = server_socket
        self.serve_dict = {0: self.register, 1: self.login, 3: self.privateChat}

    def read_file(self, file_path, data):
        with open(file_path, "r") as file:
            for line in file:
                if (
                    line.split()[0] == data["username"]
                    and line.split()[1] == data["password"]
                ):
                    return data["username"]
            return None

    def write_file(self, file_path, data):
        mark = True
        try:
            with open(file_path, "r") as file:
                for line in file:
                    if line.split()[0] == data["username"]:
                        mark = False
        except:
            pass

        if mark:
            with open(file_path, "a") as file:
                file.write(data["username"] + " " + data["password"] + "\n")
        return mark

    async def register(self, data):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, self.write_file, "UserName&PassWord", data
            )

    async def login(self, data, client_socket):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, self.read_file, "UserName&PassWord", data
            )

    async def privateChat(self):
        pass

    async def client_handler(self, client_socket, addr):
        print(f"Connected with {addr}")
        self.connected.add(client_socket)
        username = ""
        try:
            while True:
                data = await asyncio.get_event_loop().sock_recv(client_socket, 1024)
                if not data:
                    break
                data = json.loads(data)
                res = await self.serve_dict.get(data["code"], lambda: None)(data)
                if data["code"] == 0:
                    if not res:
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, "注册失败，账号已存在！".encode()
                        )
                    else:
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, "注册成功！".encode()
                        )
                elif data["code"] == 1:
                    if not res:
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, "登陆失败,帐号或密码错误！".encode()
                        )
                    else:
                        username = res
                        self.activeUser[username] = client_socket
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, "登录成功！".encode()
                        )
        except Exception as e:
            print("Error with client:", e)
        finally:
            self.connected.remove(client_socket)
            client_socket.close()
            print(f"Disconnected {addr}")

    async def serve(self):
        try:
            while True:
                client_socket, addr = await asyncio.get_event_loop().sock_accept(
                    self.server_socket
                )
                asyncio.create_task(self.client_handler(client_socket, addr))
        finally:
            self.server_socket.close()

    def run(self):
        print(f"Server is running...{self.server_socket.getsockname()}")
        asyncio.run(self.serve())
