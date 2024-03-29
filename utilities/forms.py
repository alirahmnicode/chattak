from typing import Annotated
from typing_extensions import Doc

from fastapi import Form


class UserCreateForm:

    def __init__(
        self,
        *,
        username: Annotated[
            str,
            Form(),
            Doc(
                """
                `username` string. The OAuth2 spec requires the exact field name
                `username`.
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password".
                """
            ),
        ],
    ):
        self.username = username
        self.password = password
