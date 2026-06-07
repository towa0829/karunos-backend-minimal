from pydantic import BaseModel

def convert_to_filter(data: BaseModel, op = "=="):
    filters = []
    for name, value in data.model_dump().items():
        if value is None: continue
        filters.append([name, op, value])

    return filters