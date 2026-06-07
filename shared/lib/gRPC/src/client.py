import grpc
from shared.lib.gRPC.src.utils import request_deserializer, response_serializer, readConfig
from shared.lib.basicError import errorWrapper, streamErrorWrapper

class gRPC_Client:
    def __init__(self, service_name: str):       
        """
    
        gRPC通信を行うためのクラインアントクラス

        Parameters
        ----------
            service_name: str
                接続先サービス名
        
        """

        config = readConfig()

        # TODO: 分散処理実装
        server_1 = config["services"][service_name]["server"][0] # 登録されている0番目のサーバーを使用
        host = server_1["HostName"]
        port = server_1["Port"]

        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.service_name = service_name
    
    @errorWrapper("NetworkConnectionFailed")
    def call(self, method_name: str, request_obj: dict) -> dict:
        """

        リクエスト関数（1リクエスト-1レスポンス）

        Parameters
        ----------
            method_name: str
                接続先での実行関数名

            request_obj: dict
                実行関数の引数

        Returns
        ----------
            サーバーレスポンス

        Exception
        ----------
            NetworkConnectionFailed

        """

        grpc_method = f"/{self.service_name}/{method_name}"

        stub = self.channel.unary_unary(
            grpc_method,
            request_serializer=response_serializer,
            response_deserializer=request_deserializer
        )

        response = stub(request_obj)

        return response

    @streamErrorWrapper("NetworkConnectionFailed")
    def call_server_stream(self, method_name: str, request_obj: dict):
        """

        リクエスト関数（1リクエスト-ストリーム）

        Parameters
        ----------
            method_name: str
                接続先での実行関数名

            request_obj: dict
                実行関数の引数

        Returns
        ----------
            サーバーレスポンス

        Exception
        ----------
            NetworkConnectionFailed

        """

        grpc_method = f"/{self.service_name}/{method_name}"

        stub = self.channel.unary_stream(
            grpc_method,
            request_serializer=response_serializer,
            response_deserializer=request_deserializer
        )

        responses = stub(request_obj)

        for res in responses:
            yield res

    @errorWrapper("NetworkConnectionFailed")
    def call_client_stream(self, method_name: str, request_iter):
        """

        リクエスト関数（ストリーム-1レスポンス）

        Parameters
        ----------
            method_name: str
                接続先での実行関数名

            request_obj: dict
                実行関数の引数

        Returns
        ----------
            サーバーレスポンス

        Exception
        ----------
            NetworkConnectionFailed

        """
        
        grpc_method = f"/{self.service_name}/{method_name}"

        stub = self.channel.stream_unary(
            grpc_method,
            request_serializer=response_serializer,
            response_deserializer=request_deserializer
        )

        response = stub(request_iter)

        return response

    @streamErrorWrapper("NetworkConnectionFailed")
    def call_bidi_stream(self, method_name: str, request_iter):
        """

        リクエスト関数（ストリーム-ストリーム）

        Parameters
        ----------
            method_name: str
                接続先での実行関数名

            request_obj: dict
                実行関数の引数

        Returns
        ----------
            サーバーレスポンス

        Exception
        ----------
            NetworkConnectionFailed

        """

        grpc_method = f"/{self.service_name}/{method_name}"

        stub = self.channel.stream_stream(
            grpc_method,
            request_serializer=response_serializer,
            response_deserializer=request_deserializer
        )

        for response in stub(request_iter):
            yield response
