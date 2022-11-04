import logging
from urllib.parse import urlunsplit, urlencode

import requests

from config import settings
from models import TicketAPIModel

log = logging.getLogger(__name__)
ACCOUNT = settings.API.account

headers = {
    "Authorization": f"Token token={settings.TITO_TOKEN}",
    "Accept": "application/json",
}


def get_url(account: str, event: str, page: int) -> str:
    query: str = urlencode(dict(page=page, view='extended'))
    path: str = f'/v3/{account}/{event}/tickets'
    return urlunsplit(('https', 'api.tito.io', path, query, ''))


def get_tickets(event: str):
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
    print(list(get_tickets(settings.API.event)))
