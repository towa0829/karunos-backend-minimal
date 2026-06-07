from typing import Type, get_type_hints, List
from pydantic import BaseModel 
from typing import Type, get_args, get_origin, List, Union

def model_to_prompt_structure(model: Type[BaseModel], max_depth: int = 10, indent: int = 0) -> str:
    """
    Pydantic BaseModel を簡略化した構造説明文字列に変換 (Pydantic v2対応)

    Parameters
    ----------
        model: BaseModel
            Pydantic モデルクラス

        max_depth: int
            ネストの最大深さ

        indent: int
            現在のインデントレベル

    Returns
    -------
        str: 構造説明文字列
    """
    prefix = "  " * indent
    summary = ""
    
    model_title = model.model_config.get("title")
    model_desc = model.model_config.get("description")
    if model_title or model_desc:
        summary += f"{prefix}# {model_title or ''} {model_desc or ''}\n"

    hints = get_type_hints(model)
    for field_name, field_type in hints.items():
        field_info = model.model_fields[field_name]  # v2では model_fields

        # 必須かどうか
        required = "" if getattr(field_info, 'required', True) else "Optional "
        
        # 説明文
        description = f" # {getattr(field_info, 'description', '')}" if getattr(field_info, 'description', None) else ""

        # デフォルト値
        if getattr(field_info, 'default', None) is not None:
            default_val = f" (default={field_info.default})"
        elif not getattr(field_info, 'required', True):
            default_val = " (default=None)"
        else:
            default_val = ""

        # ネストしたBaseModel
        if hasattr(field_type, "__fields__") and indent < max_depth:
            summary += f"{prefix}- {field_name} ({required}object){default_val}{description}\n"
            summary += model_to_prompt_structure(field_type, max_depth, indent + 1)

        # List型
        elif getattr(field_type, "__origin__", None) in (list, List):
            item_type = field_type.__args__[0]
            if hasattr(item_type, "__fields__") and indent < max_depth:
                summary += f"{prefix}- {field_name} ({required}List[object]){default_val}{description}\n"
                summary += model_to_prompt_structure(item_type, max_depth, indent + 1)
            else:
                summary += f"{prefix}- {field_name} ({required}List[{getattr(item_type, '__name__', str(item_type))}]){default_val}{description}\n"

        # 通常の型
        else:
            summary += f"{prefix}- {field_name} ({required}{getattr(field_type, '__name__', str(field_type))}){default_val}{description}\n"

    return summary