from __future__ import annotations

import datetime
from enum import Enum

import pydantic


class PythonLevel(Enum):
    Beginner = 1
    Intermediate = 2
    Advanced = 3
    Expert = 4


class PaginationModel(pydantic.BaseModel):
    next_page: int | None = None


class TicketModel(pydantic.BaseModel):
    first_name: str | None = ""
    last_name: str | None = ""
    name: str | None = None
    email: str | None = None
    responses: dict
    reference: str
    release_title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    speaker: bool = False
    exhibitor: bool = False

    @classmethod
    def make_empty(
        cls,
        exhibitor: bool = False,
        speaker: bool = False,
    ) -> TicketModel:
        return TicketModel(
            first_name="",
            last_name="",
            name="",
            email="",
            reference="",
            release_title="",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            speaker=speaker,
            exhibitor=exhibitor,
            responses={
                "python-experience": "Beginner",
            },
        )

    @property
    def is_updated(self):
        return self.created_at != self.updated_at

    @property
    def display_name(self) -> str:
        initial = ""
        try:
            if self.last_name:
                initial = f"{self.last_name[0]}."
        except (AttributeError, IndexError):
            initial = ""
        return f"{self.first_name} {initial}".title()

    @property
    def level(self) -> int:
        try:
            evaluation: str = self.responses.get("python-experience", "")
            return PythonLevel[evaluation].value
        except KeyError:
            return 0

    def __repr__(self):
        return f"Attendee {self.name}"


class TicketAPIModel(pydantic.BaseModel):
    tickets: list[TicketModel]
    meta: PaginationModel


class SpeakerModel(pydantic.BaseModel):
    speaker_id: str
    first_name: str
    last_name: str
    email: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
