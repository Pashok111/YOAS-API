# Other imports
from typing import Annotated, Optional, List, Literal

# Main imports
from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

from .database_dumper_v1 import (
    UserInclude, UserOrderBy, MessageInclude, MessageOrderBy
)


class Error(BaseModel):
    """
    Represents an error message.

    Attributes:
    - error (str): The error message.
    """
    error: str


class User(BaseModel):
    """
    Base for User models.

    Attributes:
    - user_id (int): the ID of the user.
    - ban_reason (Optional[str]): the reason for the user (default=None).
    - additional_info (Optional[str]): additional info for user if needed (default=None).
    """
    user_id: int
    ban_reason: Optional[str] | None = None
    additional_info: Optional[str] | None = None


class UserCreate(User):
    """
    Model for creating a User.

    Attributes:
    - user_id (int): the ID of the user.
    - ban_reason (Optional[str]): the reason for the user (default=None).
    - additional_info (Optional[str]): additional info for user if needed (default=None).
    - message (str): the messages sent by the user.
    """
    message: str


class UserResponseBase(User):
    """
    Base model for response a created User.

    Attributes:
    - user_id (int): the ID of the user.
    - ban_reason (str): the reason for the user.
    - additional_info (str): additional info for user if needed.
    - utc_created_at (float): the UTC timestamp when the message was created.
    - utc_created_at_formatted (str): the UTC timestamp when the message was created (formatted).
    """
    utc_created_at: Annotated[float, BeforeValidator(lambda t: t.timestamp())]
    utc_created_at_formatted: Annotated[
        str, BeforeValidator(lambda t: t.strftime("%Y-%m-%d %H:%M:%S"))
    ]


class UserResponse(UserResponseBase):
    """
    Model for response a created User.

    Attributes:
    - user_id (int): the ID of the user.
    - ban_reason (str): the reason for the user.
    - additional_info (str): additional info for user if needed.
    - message ("MessageResponse"): the message sent by the user.
    - utc_created_at (float): the UTC timestamp when the message was created.
    - utc_created_at_formatted (str): the UTC timestamp when the message was created (formatted).
    """
    message: "MessageResponse"


class UserResponseMessages(UserResponseBase):
    """
    Model for response a created User with many messages.

    Attributes:
    - user_id (int): the ID of the user.
    - ban_reason (str): the reason for the user.
    - additional_info (str): additional info for user if needed.
    - messages (List["MessageResponse"]): the messages sent by the user.
    - utc_created_at (float): the UTC timestamp when the message was created.
    - utc_created_at_formatted (str): the UTC timestamp when the message was created (formatted).
    """
    messages: List["MessageResponse"]


class UserFound(BaseModel):
    """
    Model for response is user found in database or not.

    Attributes:
    - found (bool): True if user found in database, False otherwise.
    - user (Optional["UserResponseMessages"]): the user if found.
    """
    found: bool
    user: Optional["UserResponseMessages"] | None = None


class MessageResponse(BaseModel):
    """
    Model for response a created Message.

    Attributes:
    - id (int): the ID of the message.
    - text (str): the text of the message.
    """
    id: int
    text: str


class MessageFound(BaseModel):
    """
    Model for response is message found in database or not.

    Attributes:
    - found (bool): True if message found in database, False otherwise.
    """
    found: bool


class DumpQueryParams(BaseModel):
    model_config = {"extra": "forbid"}

    table: Literal["users", "messages"] = "users"
    file_format: Literal["db", "csv", "json"] = "csv"
    include: List[UserInclude | MessageInclude] | None = None
    order_by: List[UserOrderBy | MessageOrderBy] | None = None
    original_db: bool = False
    indent: int | None = None
