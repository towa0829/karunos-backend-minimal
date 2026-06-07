import json
import os

from shared.lib.basicError import errorWrapper, BaseError

@errorWrapper("FileOpenError")
def readJson(file_path: str):
    if not os.path.isfile(file_path): raise BaseError("FileIsNotFount")

    with open(file_path, "r") as f:
        dict_data = json.load(f)
    
    return dict_data

@errorWrapper("FileOpenError")
def readText(file_path: str):
    if not os.path.isfile(file_path): raise BaseError("FileIsNotFount")

    with open(file_path, "r") as f:
        str_data = f.read()

    return str_data
