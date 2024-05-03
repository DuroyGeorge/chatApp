import hashlib
import json
from FileManager import FileManager
from Format import Format
import asyncio
import aiofiles


class Server:

    def __init__(self, server_socket) -> None:
        self.nameTosocket = {}
        self.socketToname = {}
        self.server_socket = server_socket
        self.fileManager = FileManager()
        self.serve_dict = {
            1: self.register,
            2: self.login,
            3: self.privateChat,
            # 4: self.publicChat,
            5: self.transQues,
            # 6: self.onFileTrans
            # 7: self.offFileTrans
        }

    async def read_file(self, file_path, data):
        lock = await self.fileManager.get_lock(file_path)
        async with lock:
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
        except Exception as e:
            print(e)

        if mark:
            lock = await self.fileManager.get_lock(file_path)
            async with lock:
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

    async def transQues(self, data, receiveFile):
        sege_num = 0
        if data["toUser"] in self.nameTosocket:
            return {"code": True, "sege_num": sege_num}
        else:
            async with aiofiles.open("receiveFileTable", "r") as f:
                async for line in f:
                    line_sp = line.split()
                    if (
                        line_sp[0] == data["fromUser"]
                        and line_sp[1] == data["toUser"]
                        and line_sp[2] == data["fileName"]
                        and line_sp[3] == data["hash"]
                    ):
                        sege_num = int(line_sp[4])
            temp = hashlib.sha256()
            temp.update(
                (
                    data["fromUser"] + data["toUser"] + data["fileName"] + data["hash"]
                ).encode()
            )
            hash = temp.hexdigest()
            receiveFile[hash] = sege_num
            return {"code": False, "sege_num": sege_num}

    async def onFileTrans(self, data, body):
        # 在线
        try:
            await asyncio.get_event_loop().sock_sendall(
                self.nameTosocket[data["toUser"]], Format(data).toBytes() + body
            )
        except:
            # 接收方掉线
            try:
                temp = {"code": 61}
                await asyncio.get_event_loop().sock_sendall(
                    self.nameTosocket[data["fromUser"]], Format(temp).toBytes()
                )
            except:
                # 发送方掉线
                temp = {"code": 61}
                await asyncio.get_event_loop().sock_sendall(
                    self.nameTosocket[data["toUser"]], Format(temp).toBytes()
                )
                raise
        try:
            # 成功发送
            temp = {"code": 60}
            await asyncio.get_event_loop().sock_sendall(
                self.nameTosocket[data["fromUser"]], Format(temp).toBytes()
            )
        except:
            # 发送方掉线
            temp = {"code": 61}
            await asyncio.get_event_loop().sock_sendall(
                self.nameTosocket[data["toUser"]], Format(temp).toBytes()
            )
            raise

    async def offFileTrans(self, data, receiveFile, body):
        temp = hashlib.sha256()
        temp.update(
            (
                data["fromUser"] + data["toUser"] + data["fileName"] + data["hash"]
            ).encode()
        )
        hash = temp.hexdigest()
        try:
            async with aiofiles.open(f"./files/{hash}", "ab") as f:
                await f.write(body)
        except:
            async with aiofiles.open(f"./files/{hash}", "wb") as f:
                await f.write(body)
        receiveFile[hash] += 1
        try:
            # 成功发送
            temp = {"code": 70}
            await asyncio.get_event_loop().sock_sendall(
                self.nameTosocket[data["fromUser"]], Format(temp).toBytes()
            )
        except:
            mark = False
            lock = await self.fileManager.get_lock("receiveFileTable")
            async with lock:
                async with aiofiles.open("receiveFileTable", "r") as f:
                    lines = await f.readlines()
                    modi_lines = []
                    for line in lines:
                        line_sp = line.split()
                        if (
                            line_sp[0] == data["fromUser"]
                            and line_sp[1] == data["toUser"]
                            and line_sp[2] == data["filename"]
                            and line_sp[3] == data["hash"]
                        ):
                            line_sp[4] = str(receiveFile[hash])
                            mark = True
                        modi_lines.append(" ".join(line_sp))
                async with aiofiles.open("receiveFileTable", "w") as f:
                    await f.writelines(modi_lines)
                if not mark:
                    async with aiofiles.open("receiveFileTable", "a") as f:
                        await f.write(
                            (
                                " ".join(
                                    [
                                        data["fromUser"],
                                        data["toUser"],
                                        data["fileName"],
                                        data["hash"],
                                        str(receiveFile[hash]),
                                    ]
                                )
                            )
                            + "\n"
                        )
                raise

    async def transferFile(self, hash, sege_num, client_socket, info):
        lock = await self.fileManager.get_lock(f"./files/{hash}")
        async with lock:
            async with aiofiles.open(f"./files/{hash}", "rb") as f:
                await f.seek(sege_num * 16 * 1024)
                while True:
                    data = await f.read(16 * 1024)
                    if not data:
                        break
                    try:
                        temp = {"code": 70, "length": len(data)} | info
                        if len(data) < 16 * 1024:
                            temp["complete"] = True
                        else:
                            temp["complete"] = False
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, Format(temp).toBytes() + data
                        )
                    except:
                        raise

    async def receive(self, client_socket):
        data = await asyncio.get_event_loop().sock_recv(client_socket, 4)
        if not data:
            # 异常失联
            return data
        length = int.from_bytes(data, "big")
        data = await asyncio.get_event_loop().sock_recv(client_socket, length)
        if not data:
            # 异常失联
            return data
        return json.loads(data)

    async def client_handler(self, client_socket, addr):
        print(f"Connected with {addr}")
        username = self.socketToname.get(client_socket, "")
        receiveFile = {}
        postFile = {}
        hashtoInfo = {}
        try:
            while True:
                data = await self.receive(client_socket)
                if not data:
                    break
                res = await self.serve_dict.get(data["code"], lambda: None)(data)
                res_dict = {}
                if data["code"] == 1:
                    if not res:
                        res_dict["code"] = 11
                    else:
                        res_dict["code"] = 10
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                elif data["code"] == 2:
                    if not res:
                        res_dict["code"] = 21
                    else:
                        username = res
                        self.nameTosocket[username] = client_socket
                        self.socketToname[client_socket] = username
                        res_dict["code"] = 20
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                    # 检查离线文件
                    lock = await self.fileManager.get_lock("compFileTable")
                    offFileHash = []
                    async with lock:
                        async with aiofiles.open("compFileTable", "r+") as f:
                            async for line in f:
                                line_sp = line.split()
                                if line_sp[1] == username:
                                    temp = hashlib.sha256()
                                    temp.update(
                                        (
                                            line_sp[0]
                                            + line_sp[1]
                                            + line_sp[2]
                                            + line_sp[3]
                                        ).encode()
                                    )
                                    hash = temp.hexdigest()
                                    offFileHash.append(hash)
                                    hashtoInfo[hash] = {
                                        "fromUser": line_sp[0],
                                        "toUser": line_sp[1],
                                        "fileName": line_sp[2],
                                        "hash": line_sp[3],
                                    }
                    if not offFileHash:
                        temp = {"code": 72, "offFileHash": offFileHash}
                        await asyncio.get_event_loop().sock_sendall(
                            client_socket, Format(temp).toBytes()
                        )
                elif data["code"] == 3:
                    if not res:
                        res_dict["code"] = 31
                    else:
                        res_dict["code"] = 30
                        res_dict["message"] = data["message"]
                    await asyncio.get_event_loop().sock_sendall(
                        client_socket, Format(res_dict).toBytes()
                    )
                elif data["code"] == 4:
                    res_dict["code"] = 40
                    res_dict["message"] = data["message"]
                    for user in self.nameTosocket:
                        await asyncio.get_event_loop().sock_sendall(
                            self.nameTosocket[user], Format(res_dict).toBytes()
                        )
                elif data["code"] == 5:
                    if not res["code"]:
                        # 文件离线发送
                        res_dict["code"] = 51
                    else:
                        # 文件在线发送
                        res_dict["code"] = 50
                    res_dict["seg_num"] = res["sege_num"]
                    await asyncio.get_event_loop().sock_sendall(
                        self.nameTosocket[username], Format(res_dict).toBytes()
                    )
                elif data["code"] == 6:
                    body = await asyncio.get_event_loop().sock_recv(
                        client_socket, data["length"]
                    )
                    await self.onFileTrans(data, body)
                elif data["code"] == 7:
                    body = await asyncio.get_event_loop().sock_recv(
                        client_socket, data["length"]
                    )
                    await self.offFileTrans(data, receiveFile, body)
                    if data["complete"]:
                        temp = hashlib.sha256()
                        temp.update(
                            (
                                data["fromUser"]
                                + data["toUser"]
                                + data["fileName"]
                                + data["hash"]
                            ).encode()
                        )
                        hash = temp.hexdigest()
                        lock = await self.fileManager.get_lock("compFileTable")
                        async with lock:
                            async with aiofiles.open("compFileTable", "a") as f:
                                await f.write(
                                    (
                                        " ".join(
                                            [
                                                data["fromUser"],
                                                data["toUser"],
                                                data["fileName"],
                                                data["hash"],
                                            ]
                                        )
                                    )
                                    + "\n"
                                )
                        receiveFile.pop(hash)
                        lock = await self.fileManager.get_lock("receiveFileTable")
                        async with lock:
                            async with aiofiles.open("receiveFileTable", "r") as f:
                                lines = await f.readlines()
                                modi_lines = []
                                for line in lines:
                                    line_sp = line.split()
                                    if (
                                        line_sp[0] == data["fromUser"]
                                        and line_sp[1] == data["toUser"]
                                        and line_sp[2] == data["filename"]
                                        and line_sp[3] == data["hash"]
                                    ):
                                        continue
                                    modi_lines.append(" ".join(line_sp))
                            async with aiofiles.open("receiveFileTable", "w") as f:
                                await f.writelines(modi_lines)
                elif data["code"] == 72:
                    postFile = data["offFileHash"]
                    for key, val in postFile.items():
                        await asyncio.create_task(
                            self.transferFile(key, val, client_socket, hashtoInfo[key])
                        )
        except Exception as e:
            # 检查是否有异常失联
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
                temp_dict = {"code": 0}
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
