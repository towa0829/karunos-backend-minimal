import json
from shared.utils.file import readJson

def request_deserializer(data: bytes):
    return json.loads(data.decode())

def response_serializer(obj):
    return json.dumps(obj).encode()


def readConfig():
    return readJson("./shared/lib/gRPC/grpc.json")