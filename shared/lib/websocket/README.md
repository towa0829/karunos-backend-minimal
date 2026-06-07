# WebSocket Manager

## WebSocket Managerとは

WebSocket ManagerとはFastAPIによるWebSocket通信を効率的に行うためのライブラリです。

## 使用方法

### 1. 初期化

```python 
router = APIRouter()
WsManager = WebSocketManager(router)
```

### 2. ルーティング

```python
@WsManager.websocket("/textbook", ArchiveTableSchema)
async def _(data: ArchiveTableSchema, manager: WebSocketManager):  
    ・・・
```

実行関数を`@WsManager.websocket`でラッピングすることでWebSocketに対応した関数を作成することができます。
`@WsManager.websocket`には2つの引数が必要です。

|  引数  | 内容 | 
|--------|-------------------------------------|
| path   | WebSocketのエンドポイント            |
| schema | エンドユーザーから送られてくるスキーマ |