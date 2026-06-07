# gRPC-library

<img src="https://grpc.io/img/logos/grpc-icon-color.png" alt="サンプル画像" width="200">

## gRPCとは

gRPCは、Googleが開発した高速・汎用・型安全なRPC（Remote Procedure Call）フレームワークです。gRPCは、異なるサービスやサーバー間で関数を呼び出すように通信できる仕組みになっており、HTTP/2をベースにしたバイナリ通信なので、高速かつ効率的な通信を実現できることが特徴です。

| 用語 | 説明 |
|------|------|
| `Servicer-method` | サーバー側で定義され、クライアントから呼び出される関数。 |
| `1リクエスト` | クライアントからサーバーに送られるリクエストが1つであることを示します。通信は一度だけ行われ、すべてのデータが1回で送信されます。 |
| `1レスポンス` | サーバーからクライアントに送られるレスポンスが1つであることを示します。通信は一度だけ行われ、すべてのデータが1回で送信されます。 |
| `ストリーム` | データが連続して大量に送信される方式。LLMの逐次生成などで利用されます。 |

## Serverの構築手順
### 1. `Servicer Class`を定義

`Servicer-method`を記述するための、`Servicer class`を定義します。

```python
from shared.lib.gRPC import Servicer

class SampleServicer(Servicer):
    def __init__(self):
        super().__init__()
```

### 2. `Servicer-method`を定義

`Servicer-method`を定義する際は必ず対象の関数を`@Servicer.method()`でラップします。

`Servicer-method`にはサーバー側が行う通信タイプに合わせて`method_type`を指定する必要があります。

| method_type | 通信タイプ（クライアント ⇄ サーバー） |
|------------|----------------------------------|
| `unary_unary` (デフォルト) | 1リクエスト - 1レスポンス |
| `unary_stream` | 1リクエスト - ストリーム |
| `stream_unary` | ストリーム - 1レスポンス |
| `stream_stream` | ストリーム - ストリーム |

```python
from shared.lib.gRPC import Servicer

class SampleServicer(Servicer):
    def __init__(self):
        super().__init__()
        
    @Servicer.method()
    def getUserName(self, user_id: str):
        ...
```

上記のコードの場合、クライアントに呼び出される関数名は`getUserNmae`であり、呼び出しにはクライアントは`user_id`を引数としてサーバー側に渡す必要があります。

※ `Servicer-method`のエラーハンドリングについて

`Servicer-method`には標準で`Basic Error Handling`が組み込まれています。そのため、`Servicer-method`内で個別にエラーハンドリングを行う必要はありません。`Servicer-method`内で発生したエラー自動的に検知され、クライアント側に返されます。

### 3. サーバーの構築・起動

サーバーの構築には「1」で定義した`Servicer Class`を`Server`に受け渡すことでサーバーの構築を行う事ができます。サーバーの起動には`Server.serve()`を実行します。

```python
from shared.lib.gRPC import Server, Servicer

class SampleServicer(Servicer):
    def __init__(self):
        super().__init__()
        
    @Servicer.method()
    def getUserName(self, user_id: str):
        ...

        return user_name
            
def main():
    server = Server(SampleServicer()) # サーバーを構築
    server.serve()                    # サーバーを起動

if __name__ == '__main__':
    main()
```

## Clientリクエストの手順

### 1. `gRPC_Client Class`の定義

引数には`Service_name`を指定します。`Service_name`は`grpc.json`に定義されています。

```python
from shared.lib.gRPC import gRPC_Client

client = gRPC_Client("LLM")
```

### 2. リクエスト

リクエストは`Servicer-method`の`method_type`に合わせて実行します。
| method_type | 通信タイプ（クライアント ⇄ サーバー） | 実行関数 |
|------------|----------------------------------|----------|
| `unary_unary` (デフォルト) | 1リクエスト - 1レスポンス | gRPC_Client.call() |
| `unary_stream` | 1リクエスト - ストリーム | gRPC_Client.call_server_stream() |
| `stream_unary` | ストリーム - 1レスポンス | gRPC_Client.call_client_stream() |
| `stream_stream` | ストリーム - ストリーム | gRPC_Client.call_bidi_stream() |

```python
from shared.lib.gRPC import gRPC_Client

client = gRPC_Client("LLM")

for netSuccess, netRes, netError in client.call_server_stream("GeneralInvoke", {
    "input": input
}):
    if netSuccess:
        serverSuccess, serverResponse, serverError = netRes
        
        if serverSuccess:
            print(serverResponse)
    
    else: raise netError
```

```python
from shared.lib.gRPC import gRPC_Client

client = gRPC_Client("User")

netSuccess, netRes, netError = client.call("getUserName", {
                                                            "user_id": "123"
                                                        })
if netSuccess:
    serverSuccess, serverResponse, serverError = netRes
    
    if serverSuccess:
        print(serverResponse)

else: raise netError
```

