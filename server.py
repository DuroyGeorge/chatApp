import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from Format import Format
import asyncio
import aiofiles


class Server:

    def __init__(self, server_socket) -> None:
        self.nameTosocket = {}
        self.socketToname = {}
        self.server_socket = server_socket
        self.serve_dict = {
            0: self.register,
            1: self.login,
            2: self.privateChat,
            # 3: self.publicChat,
            4: self.transQues,
            # 5: self.transferFile
        }

    async def read_file(self, file_path, data):
        async with aiofiles.open(file_path, mode="r") as file:
            async for line in file:
                username, password = line.strip().split()
                if username == data["username"] and password == data["password"]:
                    return True
                return False

    async def write_file(self, file_path, data):
        mark = True
        try:
            async with aiofiles.open(file_path, "r") as file:
                async for line in file:
                    if line.split()[0] == data["username"]:
                        mark = False
        except:
            pass

        if mark:
            async with asyncio.Lock():
                async with aiofiles.open(file_path, "a") as file:
                    await file.write(data["username"] + " " + data["password"] + "\n")
        return mark

    async def register(self, data):
        return await self.write_file("UserName&PassWord", data)

    async def login(self, data):
        return await self.read_file("UserName&PassWord", data)

    async def privateChat(self, data):
        if data["toUser"] in self.nameTosocket:
            return data["toUser"]
        else:
            return None

    async def transQues(self, data):
        sege_num = 0
        try:
            async with aiofiles.open("files", "r") as f:
                async for line in f:
                    line_sp = line.split()
                    if (
                        line_sp[0] == data["fromUser"]
                        and line_sp[1] == data["toUser"]
                        and line_sp[2] == data["fileName"]
                        and line_sp[3] == data["hash"]
                    ):
                        sege_num = line_sp[4]
        except:
            async with aiofiles.open("files", "a") as f:
                pass
        if data["toUser"] in self.nameTosocket:
            return {"code": True, "sege_num": sege_num}
        else:
            return {"code": False, "sege_num": sege_num}

    async def transferFile(self, data, username, fileTrans):
        temp = hashlib.sha256()
        temp.update(data["fromUser"] + data["toUser"] + data["fileName"] + data["hash"])
        hash = temp.hexdigest()
        sege_num = 0
        if hash in fileTrans:
            sege_num = fileTrans[hash]
        else:
            fileTrans[hash] = sege_num
        if data["onLine"]:
            pass
        else:
            pass

    async def receive(self, client_socket, addr, username):
        data = await asyncio.get_event_loop().sock_recv(client_socket, 4)
        if not data:
            # 异常失联
            self.nameTosocket.pop(username, None)
            client_socket.close()
            print(f"Disconnected {addr}")
        length = int.from_bytes(data, "big")
        data = await asyncio.get_event_loop().sock_recv(client_socket, length)
        if not data:
            # 异常失联
            self.nameTosocket.pop(username, None)
            client_socket.close()
            print(f"Disconnected {addr}")
        return json.loads(data)

    async def client_handler(self, client_socket, addr):
        print(f"Connected with {addr}")
        username = self.socketToname.get(client_socket, "")
        fileTrans = {}
        try:
            while True:
                data = self.receive(client_socket, addr, username)
                res = await self.serve_dict.get(data["code"], lambda: None)(data)
                res_dict = {}
                if data["code"] == 0:
                    if not res:
                        res_dict["message"] = "注册失败，账号已存在！"
                    else:
                        res_dict["message"] = "注册成功！"
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                elif data["code"] == 1:
                    if not res:
                        res_dict["message"] = "登陆失败,帐号或密码错误！"
                    else:
                        username = res
                        self.nameTosocket[username] = client_socket
                        self.socketToname[client_socket] = username
                        res_dict["message"] = "登录成功！"
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                elif data["code"] == 2:
                    if not res:
                        res_dict["message"] = "对方不在线！"
                    else:
                        res_dict["message"] = data["message"]
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                elif data["code"] == 3:
                    res_dict["message"] = data["message"]
                    for user in self.nameTosocket:
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[user], Format(res_dict).toBytes()
                        )
                elif data["code"] == 4:
                    if not res["code"]:
                        # 文件转为离线发送
                        res_dict["message"] = "是否愿意离线发送？"
                        res_dict["seg_num"] = res["sege_num"]
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[username], Format(res_dict).toBytes()
                        )
                    else:
                        # 文件在线发送
                        res_dict["message"] = "文件正在发送！"
                        res_dict["seg_num"] = res["sege_num"]
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[username], Format(res_dict).toBytes()
                        )
                elif data["code"] == 5:
                    await self.transferFile(data, username, fileTrans)

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
                temp_dict = {"message": "与服务器连接成功！"}
                await asyncio.get_event_loop().sock_sendall(
                    client_socket, Format(temp_dict).toBytes()
                )
                asyncio.create_task(self.client_handler(client_socket, addr))
        finally:
            self.server_socket.close()

    def run(self):
        print(f"Server is running...{self.server_socket.getsockname()}")
        asyncio.run(self.serve())
        print("Server closed")
