from enum import Enum
import logging

log = logging.getLogger(__name__)


class PythonLevel(Enum):
    Beginner = 1
    Intermediate = 2
    Advanced = 3
    Expert = 4


class Attendee:
    def __init__(self, loaded_schema):
        for attribute, value in loaded_schema.items():
            setattr(self, attribute, value)
        self.in_anomaly = False

    @property
    def level(self):
        evaluation = self.responses.get("your-python-experience")
        try:
            return PythonLevel[evaluation].value
        except KeyError:
            return 0

    @property
    def display_name(self):
        try:
            return "{first} {initial}.".format(
                first=self.first_name.title(), initial=self.last_name.title()[0]
            )
        except (IndexError, AttributeError):
            self.in_anomaly = True
            log.warning("XXX Fix ticket %s", self.reference)
            return "XXX Fix ticket XXX"

    @property
    def speaker(self):
        """
        Could be determined from either
        - a list of emails
        - an API call to sessionize or similar
        - name or slug of the ticker release
        """
        return False

    @property
    def exhibitor(self):
        return False

    def __repr__(self):
        return f"<Attendee {self.reference} {self.name}>"
