import os
import json

from shared.lib.basicError.src.errorKey import ErrorKey

LANG = "ja"

with open("./shared/lib/basicError/ErrorCode.json", "r") as f:
    ERRORS = json.load(f)

class BasicError(Exception):
    def __init__(self, key: ErrorKey, code = None, message = None):
        """
        
        BasicError クラス

        Parameters
        ----------
            key: str
                エラーキー
            
            code: str, optional
                エラーコード。指定しない場合、ErrorCode.json のコードが使用される。

            message: str, optional
                エラーメッセージ。指定しない場合、ErrorCode.json のメッセージが使用される。
        
        """

        error = ERRORS[key]

        if code is not None: self.code = code
        else: self.code = f"{error["category"]}-{error["code"]}"

        if message is not None: self.message = message
        else: self.message = f"[{message['message'][LANG]}]"

        super().__init__(f"[{self.code}] {self.message}")

def errorWrapper(key: ErrorKey, service_prefix = os.getenv("ERROR_PREFIX", "")):
    """
    
    通常のエラーハンドリングを行うデコレータ

    Parameters
    ----------
        key: str
            エラーキー
        
        service_prefix: str, optional
            サービスプレフィックス。環境変数 "ERROR_PREFIX" から取得され、指定しない場合は空文字列が使用される。
    
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            error = ERRORS[key]

            code = f"{error["category"]}-{error["code"]}"
            message = error["message"][LANG]

            try:
                result = func(*args, **kwargs)

                return True, result, None
            except BasicError as e:
                print(e, flush=True)
                return (
                    False,
                    None,
                    e
                )
            except Exception as e:
                print(e, flush=True)

                return  (
                    False,
                    None,
                    BasicError(
                        key,
                        code if service_prefix == "" else f"{service_prefix}-{code}",
                        f"({message})\n{e}"
                    )
                )
            
        return wrapper
    return decorator

def streamErrorWrapper(key: ErrorKey, service_prefix = os.getenv("ERROR_PREFIX", "")):
    """
    
    ストリーム処理用のエラーハンドリングを行うデコレータ

    Parameters
    ----------
        key: str
            エラーキー

        service_prefix: str, optional
            サービスプレフィックス。環境変数 "ERROR_PREFIX" から取得され、指定しない場合は空文字列が使用される。

    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            error = ERRORS[key]

            code = f"{error["category"]}-{error["code"]}"
            message = error["message"][LANG]

            try:
                for res in func(*args, **kwargs):
                    yield True, res, None
            except BasicError as e:
                return (
                    False,
                    None,
                    e
                )
            except Exception as e:
                return  (
                    False,
                    None,
                    BasicError(
                        key,
                        code if service_prefix == "" else f"{service_prefix}-{code}",
                        f"({message})\n{e}"
                    )
                )
            
        return wrapper
    return decorator

