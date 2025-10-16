"""Shared message schema used in API responses."""

from pydantic import BaseModel


class Msg(BaseModel):
    """Represents a simple message response payload."""

    msg: str
