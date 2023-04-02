import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    status_code: int
    body: dict

    def to_response(self) -> dict:
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": self.status_code,
            "body": json.dumps(self.body)
        }

    @staticmethod
    def success(message: str = '') -> dict:
        return Response(200, {"message": message}).to_response()

    @staticmethod
    def unauthorized(message: str = '') -> dict:
        return Response(401, {"message": message}).to_response()

    @staticmethod
    def unexpected(message: str = '') -> dict:
        return Response(500, {"message": message}).to_response()
