import asyncio
from concurrent.futures import ThreadPoolExecutor


def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read()


def write_file(file_path, data):
    with open(file_path, "w") as file:
        file.write(data)


async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        # 异步写文件
        await loop.run_in_executor(
            executor, write_file, "example.txt", "Hello, ThreadPoolExecutor!"
        )
        # 异步读文件
        content = await loop.run_in_executor(executor, read_file, "example.txt")
        print(content)


asyncio.run(main())
