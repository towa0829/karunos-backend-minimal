# CRUD-library

## CRUD-libraryについて

CRUD-libraryとはDB操作（Create, Read, Update, Delete）の処理を容易に行うためのライブラリです。SQLAlchemyをベースに開発されています。

## 使用方法について

### 1. 初期化

```python
from models.ArchiveTable import ArchiveTable
from core.db import session
from shared.lib.crud.crud import CRUD

archive_crud = CRUD(session, ArchiveTable)
```

### 2. CREATE・READ・UPDATE・DELETE

- CREATE

```python
@router.post("/", response_model=ArchiveTableSchema)
async def _(data: ArchiveTableSchema):
    success, result, error = archive_crud.create(data)

    return result
```

- READ

```python
success, valid_tokens, error = auth_crud.read([
    ["token", "==", token],                 # 条件1
    ["expires_at", ">=", get_utc_time()],   # 条件2
    ["used_at", "==", None]                 # 条件3
])  
```

- UPDATE

```python
success, new_archive, error = archive_crud.update(
    [
        ["id", "==", data.id] # 条件
    ],
    {
        "contents": new_contents,
        "archive_status": "RUNNING"
    } # 更新内容 
)
```

- DELETE

```python
success, deleted_memos, error = memo_crud.delete([
    ["id", "==", memo_id] # 条件
])
```
