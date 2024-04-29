import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import websockets


connected = set()


def read_file(file_path, data):
    with open(file_path, "r") as file:
        for line in file:
            if (
                line.split()[0] == data["username"]
                and line.split()[1] == data["password"]
            ):
                return True
        return False


def write_file(file_path, data):
    with open(file_path, "r") as file:
        for line in file:
            if line.split()[0] == data["username"]:
                return False
    with open(file_path, "a") as file:
        file.write(data["username"] + " " + data["password"] + "\n")
        return True


async def register(data):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, write_file, "UserName&PassWord", data
        )


async def login(data):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, read_file, "UserName&PassWord", data
        )


async def wrongCode():
    pass


serve_dict = {0: register, 1: login}


async def chat_handler(websocket):
    connected.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            res = await serve_dict.get(data["code"], lambda: None)(data)
            if data["code"] == 0:
                if not res:
                    await websocket.send("注册失败，账号已存在！")
                else:
                    await websocket.send("注册成功！")
            elif data["code"] == 1:
                if not res:
                    await websocket.send("登陆失败,帐号或密码错误！")
                else:
                    await websocket.send("登录成功！")
    except:
        print("客户端意外断开连接！")
    finally:
        connected.remove(websocket)
        print("Client disconnected")


# 启动服务器
async def main():
    async with websockets.serve(chat_handler, "localhost", 8765):
        print("Server started at ws://localhost:8765")
        await asyncio.Future()  # 运行服务器直到被手动停止


# 运行事件循环
asyncio.run(main())
