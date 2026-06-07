import uuid6
import random
import string

def gen_uuid7():
    return uuid6.uuid7()

def random_string(length: int = 16) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))