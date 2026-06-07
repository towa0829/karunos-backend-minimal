from shared.lib.basicError.src.main import BasicError
from shared.lib.basicError.src.main import errorWrapper
import requests

# TODO: エラーハンドリング
class Client:

    @errorWrapper("InvalidFormat")
    def __init__(self, key: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type" : "application/json",
            "Accept": "application/json"
        })
        if key:
            self.session.headers.update({
                "Authorization": f"Bearer {key}"
            })
            
    @errorWrapper("NetworkConnectionFailed")
    def get(self, url:str, params:dict = None) -> dict:
        response = self.session.get(url, params=params)

        return self._handle_response(response)
    
    @errorWrapper("NetworkConnectionFailed")
    def post(self, url: str, data: dict = None) -> dict:
        response = self.session.post(url, json=data)

        return self._handle_response(response)
    
    @errorWrapper("NetworkConnectionFailed")
    def put(self, url:str, data:dict = None) -> dict:
        response = self.session.put(url, json=data)

        return self._handle_response(response)
    
    @errorWrapper("NetworkConnectionFailed")
    def delete(self, url: str, data: dict = None) -> dict:
        response = self.session.delete(url, json=data)

        return self._handle_response(response)
    
    
    def _handle_response(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"API Error {response.status_code}: {response.text}") from e
        except ValueError:
            raise RuntimeError("Invalid JSON response")