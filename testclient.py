import asyncio
import websockets
import json  # 导入 json 模块


async def client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 获取用户名和密码
        username = input("Username: ")
        password = input("Password: ")

        message = json.dumps({"code": 0, "username": username, "password": password})

        await websocket.send(message)
        print("> Sent:", message)
        response = await websocket.recv()
        print("> recv:", response)


asyncio.run(client())
