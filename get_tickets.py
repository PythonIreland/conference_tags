import logging
from pprint import pprint

import requests

from config import settings
from schema import TicketAPISchema

log = logging.getLogger(__name__)
ACCOUNT = settings.API.account

headers = {
    "Authorization": f"Token token={settings.TITO_TOKEN}",
    "Accept": "application/json",
}


def get_tickets(event):
    """retrieves tickets from API and extract relevant data"""
    t_schema = TicketAPISchema()
    page = 1
    # while page < 2:
    while page is not None:
        log.debug("getting page %d", page)
        r = requests.get(
            f"https://api.tito.io/v3/{ACCOUNT}/{event}/tickets?page={page}&view=extended",
            headers=headers,
        ).json()
        data = t_schema.load(r)
        for ticket in data["tickets"]:
            yield ticket
        page = data["meta"]["next_page"]


if __name__ == "__main__":
    pprint([ticket for ticket in get_tickets(settings.API.event)])
