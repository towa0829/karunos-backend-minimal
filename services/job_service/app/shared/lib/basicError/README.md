# basicError-libaray

## basicErrorとは

basicErrorとはKarynos全体において共通したエラーハンドリングを実現するためのライブラリです。標準の例外処理をラップして統一的なエラーコード・メッセージ管理を提供します。

## 使用方法について

### エラーの発生

```python
from shared.lib.basicError.src.basicError import BasicError

# エラーの発生
raise BasicError("InvalidFormat") # "InvalidFormat"発生時
```

`BasicError`の引数にはErrorKeyを挿入します。

`InvalidFormat`の場合エラーコード・エラーメッセージは下記のようになります。

| 項目 | 内容 |
|----- |------|
| ErrorKey | InvalidFormat |
| code | 12001 |
| category | VAL |
| message | 値の形式不正 |

### 関数ラッピング

```python
from shared.lib.basicError.src.basicError import BasicError
from shared.lib.basicError.src.basicError import errorWrapper

@errorWrapper("InvalidFormat")
def my_function(x):
    if x < 0:
        raise BasicError("ValueOutOfRange")
    return x * 2

success, result, error = my_function(10)

"""

try:
    return my_function(x)
catch Exception as e:
    return e


"""
```

関数に対して対してエラーハンドリングを適用させる場合は上記のように対象の関数を`errorWrapper`でラッピングします。`errorWrapper`の引数にはErrorKeyを挿入します。`errorWrapper`に引数に指定されるErrorKeyはデフォルトのエラーメッセージとなります。つまり、関数内で発生したエラーのうち、動的に`raise`されたもの以外（今回の場合`raise BasicError("ValueOutOfRange")`以外）でエラーが発生した場合のErrorKeyとなります。

そのため今回のエラーハンドリングは下記のようになります。
| 入力 | 出力 |
|------|-----|
| `x = 2` | `4` | 
| `x = -4` | `BasicError("ValueOutOfRange")` | 
| `x = "hello"` |  `BasicError("InvalidFormat")` <br><br> ※本来なら`TypeError: '<' not supported between instances of 'str' and 'int'`が発生し、処理が停止しますがerrorWrapperでラッピングされているためデフォルトエラーの`BasicError("InvalidFormat")`が出力されます |

#### 出力について
`errorWrapper`でラッピングされている関数の出力は必ず下記のタプル型で出力されます。

| 項目 | 内容 |
|------|-----|
| 第1項：`bool` | 処理成功の可否 |
| 第2項：`any` | 処理成功時の関数返り値 |
| 第3項：`BasicError` | エラー発生時の返り値 |

## ErrorKeyについて

basicErrorではエラーコードとエラーメッセージを統一して管理するためにErrorKeyによって共通したエラーコードとエラーメッセージを呼び出すように設計されています。下記はErrorKeyとエラーコード・エラーメッセージの一覧です。

| エラーキー | コード | カテゴリ | メッセージ（日本語） |
| --- | --- | --- | --- |
| MissingRequiredParameter | 11001 | VAL | 必須パラメータ不足 |
| InvalidFormat | 12001 | VAL | 値の形式不正 |
| ValueOutOfRange | 12002 | VAL | 範囲外の値 |
| DuplicateInput | 13001 | VAL | 入力値が既存データと重複 |
| RelatedResourceNotFound | 14001 | VAL | 関連リソースが存在しない |
| AuthenticationMissing | 21001 | AUTH | 認証情報不足 |
| AuthenticationFailed | 21002 | AUTH | 認証失敗 |
| InsufficientPermissions | 22001 | AUTH | 権限不足 |
| SessionExpired | 23001 | AUTH | セッション期限切れ |
| MfaIncomplete | 24001 | AUTH | 多要素認証未完了 |
| AccountLocked | 25001 | AUTH | アカウントロック / 無効化済みユーザー |
| RecordNotFound | 31001 | DB | レコード未検出 |
| QueryError | 32001 | DB | クエリエラー |
| TransactionConflict | 33001 | DB | トランザクション競合 |
| DuplicateKeyError | 33002 | DB | 重複キーエラー |
| DatabaseConnectionFailed | 34001 | DB | DB接続失敗 |
| StorageFull | 35001 | DB | ストレージ容量不足 |
| ExternalApiAuthFailed | 41001 | EXT | 外部API認証失敗 |
| ExternalApiInvalidResponse | 42001 | EXT | 外部APIレスポンス不正 |
| ExternalApiTimeout | 43001 | EXT | 外部APIタイムアウト |
| ExternalServiceDown | 43002 | EXT | 外部サービスがダウン |
| ThirdPartySdkError | 44001 | EXT | サードパーティSDKエラー |
| ExternalSystemTemporaryLimit | 45001 | EXT | 外部システム依存の一時的制限 |
| ServerInternalException | 51001 | SYS | サーバー内部例外 |
| InvalidConfigFile | 52001 | SYS | 設定ファイル不正 |
| OutOfMemory | 53001 | SYS | メモリ不足 |
| DiskSpaceInsufficient | 53002 | SYS | ディスク容量不足 |
| ServiceStartupFailed | 54001 | SYS | サービス起動失敗 |
| InternalInconsistency | 55001 | SYS | 内部不整合 |
| FileIsNotFount | 54002 | SYS | 無効なファイルパス |
| FileOpenError | 52002 | SYS | ファイル読み込みエラー |
| NetworkConnectionFailed | 61001 | NET | ネットワーク接続失敗 |
| DnsResolutionFailed | 62001 | NET | DNS解決失敗 |
| CommunicationTimeout | 63001 | NET | 通信タイムアウト |
| LoadBalancingFailed | 64001 | NET | 負荷分散ルーティング失敗 |
| InterServiceAuthError | 65001 | NET | サービス間通信認証エラー |
| RequestLimitExceeded | 81001 | RATE | リクエスト数超過 |
| ApiKeyLimitExceeded | 82001 | RATE | APIキー利用制限超過 |
| BandwidthLimitExceeded | 83001 | RATE | 帯域幅制限 |
| TemporaryBlockForProtection | 85001 | RATE | システム保護のための一時ブロック |
| UnknownError | 91001 | UNK | 未知のエラー |
| UnclassifiedSystemException | 92001 | UNK | 未分類のシステム例外 |
| FallbackError | 99999 | UNK | フォールバック（汎用キャッチオール） |
