import logging
import time
from typing import Dict

import jwt
import requests
from attr import attr
from typing_extensions import Literal

from . import err


@attr.s
class APIClientBase:
    api_key: str
    api_secret: str

    name = 'zoom_api_client'
    user_id: str = 'me'
    base_url: str = 'https://api.zoom.us/v2'

    def bearer_token(self) -> str:
        return self.generate_jwt(self.api_key, self.api_secret)

    def make_request(
            self,
            endpoint: str,
            method: Literal["GET", "POST", "PATCH", "DELETE", 'PUT'],
            query: Dict = None,
            body: Dict = None,
            raise_on_error=True,
    ) -> requests.Response:
        allowed_methods = "GET POST PATCH DELETE PUT".split()
        if method not in allowed_methods:
            raise ValueError(
                f'Invalid method: {method}. Must be one of {", ".join(allowed_methods)}'
            )
        headers = {"Authorization": f"Bearer {self.bearer_token()}"}
        url = self.base_url + endpoint
        logging.debug(f"Making {method} request to {endpoint}")
        session = requests.Session()

        r = session.request(method, url, headers=headers, params=query, json=body)

        if 200 <= r.status_code < 300:
            return r

        try:
            message = r.json()["_error"]["message"]
        except KeyError:
            message = r.json()

        logging.error(f"Unsuccessful request to {r.url}: [{r.status_code}] {message}")

        logging.debug(f"Full response: {r.json()}")
        logging.debug(f"Headers: {r.headers}")
        logging.debug(f"Params: {query}")
        logging.debug(f"Body: {body}")
        if not raise_on_error:
            logging.warning(
                f"raise_on_error is False, ignoring API error and returning response"
            )
            return r

        if r.status_code in err.HTTP_ERRORS_MAP:
            raise err.HTTP_ERRORS_MAP[r.status_code](message)
        else:
            raise err.APIError(message)

    def get(
            self, endpoint: str, query: Dict = None, raise_on_error: bool = True
    ) -> requests.Response:
        return self.make_request(
            endpoint, method="GET", query=query, raise_on_error=raise_on_error
        )

    def post(
            self,
            endpoint: str,
            query: Dict = None,
            body: Dict = None,
            raise_on_error: bool = True,
    ) -> requests.Response:
        return self.make_request(
            endpoint,
            method="POST",
            query=query,
            body=body,
            raise_on_error=raise_on_error,
        )

    def patch(
            self,
            endpoint: str,
            query: Dict = None,
            body: Dict = None,
            raise_on_error: bool = True,
    ) -> requests.Response:
        return self.make_request(
            endpoint,
            method="PATCH",
            query=query,
            body=body,
            raise_on_error=raise_on_error,
        )

    def put(
            self,
            endpoint: str,
            query: Dict = None,
            body: Dict = None,
            raise_on_error: bool = True,
    ) -> requests.Response:
        return self.make_request(
            endpoint,
            method="PUT",
            query=query,
            body=body,
            raise_on_error=raise_on_error,
        )

    def delete(
            self,
            endpoint: str,
            query: Dict = None,
            body: Dict = None,
            raise_on_error: bool = True,
    ) -> requests.Response:
        return self.make_request(
            endpoint,
            method="DELETE",
            query=query,
            body=body,
            raise_on_error=raise_on_error,
        )

    @staticmethod
    def generate_jwt(key, secret):
        header = {"alg": "HS256", "typ": "JWT"}

        payload = {"iss": key, "exp": int(time.time() + 3600)}

        token = jwt.encode(payload, secret, algorithm="HS256", headers=header)
        return token.decode("utf-8")
