from pydantic import BaseModel, create_model, ConfigDict
from sqlalchemy.inspection import inspect
from typing import Any
from uuid import UUID

def sqlalchemy_to_pydantic(table) -> BaseModel:
    mapper = inspect(table)
    fields: dict[str, tuple[Any, Any]] = {}

    for column in mapper.columns:
        try:
            py_type = column.type.python_type
        except:
            py_type = Any

        fields[column.key] = (py_type | None, None)

    return create_model(
        f"{table.__name__}Schema", 
        __pydantic_config__=ConfigDict(from_attributes=True),
        **fields
    )