import json


class Format:
    def __init__(self, data) -> None:
        self.data = data
        self.length = len(json.loads(data))

    @classmethod
    def fromBytes(cls, jsonData):
        temp = json.loads(jsonData)
        return cls(temp)

    def toBytes(self):
        length_bytes = self.length.to_bytes(4, "big")
        message_bytes = json.dumps(self.data).encode("utf-8")
        return length_bytes + message_bytes
