import datetime

import pydantic

from attendees import PythonLevel


class PaginationModel(pydantic.BaseModel):
    next_page: int | None = None


class TicketModel(pydantic.BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    email: str | None = None
    responses: dict
    reference: str
    release_title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    speaker: bool = False

    @property
    def is_updated(self):
        return self.created_at != self.updated_at

    @property
    def display_name(self) -> str:
        try:
            initial = self.last_name.title()[0]
        except (AttributeError, IndexError):
            initial = ""
        return f"{self.first_name} {initial}."

    @property
    def exhibitor(self) -> bool:
        return False

    @property
    def level(self) -> int:
        try:
            evaluation = self.responses.get("python-experience")
            return PythonLevel[evaluation].value
        except KeyError:
            return 0


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
