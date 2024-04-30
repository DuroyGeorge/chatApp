import json
from concurrent.futures import ThreadPoolExecutor
import asyncio


class Server:

    def __init__(self, server_socket) -> None:
        self.nameTosocket = {}
        self.socketToname = {}
        self.server_socket = server_socket
        self.serve_dict = {
            0: self.register,
            1: self.login,
            3: self.privateChat,
            # 4: self.publicChat,
            4: self.privateFile,
        }

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

    async def login(self, data):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, self.read_file, "UserName&PassWord", data
            )

    async def privateChat(self, data):
        if data["toUser"] in self.nameTosocket:
            return data["toUser"]
        else:
            return None

    async def privateFile(self, data):
        if data["toUser"] in self.nameTosocket:
            return True
        else:
            return False

    async def client_handler(self, client_socket, addr):
        print(f"Connected with {addr}")
        username = self.socketToname.get(client_socket, "")
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
                        self.nameTosocket[username] = client_socket
                        self.socketToname[client_socket] = username
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, "登录成功！".encode()
                        )
                elif data["code"] == 3:
                    if not res:
                        if data["toName"] == username:
                            await asyncio.get_event_loop().sock_sendall(
                                client_socket, "不要私聊自己！".encode()
                            )
                        else:
                            await asyncio.get_event_loop().sock_sendall(
                                client_socket, "对方不在线！".encode()
                            )

                    else:
                        text = f"{username}\n   {data['message']}"
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[res], text.encode()
                        )
                elif data["code"] == 4:
                    text = f"{username}\n   {data['message']}"
                    for user in self.nameTosocket:
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[user], text.encode()
                        )
                elif data["code"] == 5:
                    if not res:
                        # 文件转为离线发送
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[username], "是不是愿意离线发送？".encode()
                        )
                        yes = await asyncio.get_event_loop().sock_recv(
                            self.nameTosocket[username], 1024
                        )
                        if yes:
                            pass
                    else:
                        with ThreadPoolExecutor() as excutor:
                            await asyncio.get_event_loop().run_in_executor(
                                excutor, self.client_handler, client_socket, addr
                            )

        except Exception as e:
            print("Error with client:", e)
        finally:
            self.nameTosocket.pop(username, None)
            client_socket.close()
            print(f"Disconnected {addr}")

    async def serve(self):
        try:
            while True:
                client_socket, addr = await asyncio.get_event_loop().sock_accept(
                    self.server_socket
                )
                await asyncio.get_event_loop().sock_sendall(
                    client_socket, "与服务器连接成功！".encode()
                )
                asyncio.create_task(self.client_handler(client_socket, addr))
        finally:
            self.server_socket.close()

    def run(self):
        print(f"Server is running...{self.server_socket.getsockname()}")
        asyncio.run(self.serve())
