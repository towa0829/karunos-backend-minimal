from typing import Literal

import grpc
from grpc import Server
from concurrent import futures
import time
import os
import functools

from shared.lib.gRPC.src.utils import request_deserializer, response_serializer, readConfig
from shared.lib.basicError import errorWrapper, streamErrorWrapper

# デフォルトポート：50000
DOCKER_PORT = os.getenv("DOCKER_PORT", 50000)

class Servicer:
    def __init__(self):
        """
        
        gRPCに実行関数を登録するためのクラス

        Parameters
        ----------
            None
        
        """

        config = readConfig()       
        self.service_name = os.getenv("SERVICE_NAME")
        self.methods = config["services"][self.service_name]["Methods"]

    @staticmethod
    def method(method_type: Literal["unary_unary", "unary_stream", "stream_unary", "stream_stream"]  = "unary_unary"):
        """
        
        サーバー登録用の関数ラッパー

        Parameters
        ----------
            method_type: str = "unary_unary"
                リクエスト・レスポンスタイプの設定
                
                unary_unary: 1リクエスト-1レスポンス
                unary_stream: 1リクエスト-ストリーム
                stream_unary: ストリーム-1レスポンス
                stream_stream: ストリーム-ストリーム

        """

        def decorator(func):
            if method_type in ["unary_stream", "stream_stream"]:
                wrapper_decorator = streamErrorWrapper("NetworkConnectionFailed")
            else:
                wrapper_decorator = errorWrapper("NetworkConnectionFailed")

            @functools.wraps(func)
            @wrapper_decorator
            def wrapper(self, request, context):
                # TODO: 認証処理の実装
                
                return func(self, **request)
            
            wrapper._method_info = {"method_type": method_type}
            return wrapper
        return decorator


class Server():
    def __init__(self, servicer: Servicer):
        """
    
        gRPC通信を行うためのサーバークラス

        Parameters
        ----------
            servicer: Servicer
                サービス関数を定義するクラス
        
        """
        
        self.servicer = servicer
        self.service_name = servicer.service_name
        self.methods = servicer.methods

    def serve(self):
        """
        
        gRPCサーバーの開始

        Parameters
        ----------
            None

        Returns
        ---------
            None
        
        """

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) # max_workersはスレッドの最大数を指定
        self.add_servicer_to_server(
            servicer = self.servicer,
            server = server,
            service_name = self.service_name,
            methods=self.methods
        )

        server.add_insecure_port(f"[::]:{DOCKER_PORT}")

        print(f"Starting server. Listening on port {DOCKER_PORT}.", flush=True)
        
        server.start()

        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)

    def add_servicer_to_server(self, servicer: Servicer, server: Server, service_name: str, methods: list[str]):
        """
        
        サーバーにServicerの関数を登録

        Parameters
        ----------
            servicer: Servicer
                登録するServicer

            server: Server
                gRPCサーバークラス

            service_name: str
                Servicer名

            methods: lsit[str]
                Servicerに登録されている関数名 

        Returns
        ---------
            None
        
        """

        rpc_method_handlers = {}

        for method_name in methods:
            method_type = getattr(self.servicer, method_name)._method_info["method_type"]
            if method_type == "unary_unary":
                handler = grpc.unary_unary_rpc_method_handler(
                    getattr(servicer, method_name),
                    request_deserializer=request_deserializer,
                    response_serializer=response_serializer
                )
            elif method_type == "unary_stream":
                handler = grpc.unary_stream_rpc_method_handler(
                    getattr(servicer, method_name),
                    request_deserializer=request_deserializer,
                    response_serializer=response_serializer
                )
            elif method_type == "stream_unary":
                handler = grpc.stream_unary_rpc_method_handler(
                    getattr(servicer, method_name),
                    request_deserializer=request_deserializer,
                    response_serializer=response_serializer
                )
            elif method_type == "stream_stream":
                handler = grpc.stream_stream_rpc_method_handler(
                    getattr(servicer, method_name),
                    request_deserializer=request_deserializer,
                    response_serializer=response_serializer
                )

            rpc_method_handlers[method_name] = handler

        generic_handler = grpc.method_handlers_generic_handler(
            service_name, rpc_method_handlers
        )
        server.add_generic_rpc_handlers((generic_handler,))

