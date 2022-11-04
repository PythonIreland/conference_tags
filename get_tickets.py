import logging
from urllib.parse import urlunsplit, urlencode

import requests

from config import settings
from models import TicketAPIModel
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


def get_url(account: str, event: str, page: int) -> str:
    query: str = urlencode(dict(page=page, view='extended'))
    path: str = f'/v3/{account}/{event}/tickets'
    return urlunsplit(('https', 'api.tito.io', path, query, ''))


def get_tickets_new(event):
    page: int | None = 1
    while page is not None:
        response = requests.get(get_url(ACCOUNT, event, page), headers=headers)
        response.raise_for_status()

        instance = TicketAPIModel.parse_obj(response.json())
        for ticket in instance.tickets:
            if not ticket.email:
                continue
            yield ticket
        page = instance.meta.next_page


if __name__ == "__main__":
    print(get_url(settings.API.account, settings.API.event, 1))
    print(list(get_tickets_new(settings.API.event)))
    # pprint([ticket for ticket in get_tickets(settings.API.event)])
