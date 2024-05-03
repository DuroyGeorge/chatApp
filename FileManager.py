import asyncio


class FileManager:
    def __init__(self):
        self.locks = {}

    async def get_lock(self, file_path):
        if file_path not in self.locks:
            self.locks[file_path] = asyncio.Lock()
        return self.locks[file_path]
