import requests
from pprint import pprint
from collections import namedtuple
from urllib.parse import urlparse
from config import settings

# Tito uses API keys to allow access to the API.
# You can find your API key by signing in at https://api.tito.io.
import logging
import os
from schema import TicketAPISchema

# auth_key = os.getenv("TITO_TOKEN")
auth_key = settings.TITO_TOKEN
token = "Token token={}".format(auth_key)
# ACCOUNT = "python-ireland"
ACCOUNT = settings.API.account
# event = "pycon-limerick-2020"
# event = "pycon-ireland-2018"
event = settings.API.event
log = logging.getLogger(__name__)

base_url = "https://api.tito.io/v3/{account}/{event}".format(
    account=ACCOUNT, event=event
)

Attendee = namedtuple(
    "Attendee",
    (
        "display_name",
        "full_name",
        "email",
        "reference",
        "level",
        "exhibitor",
        "speaker",
        "lunch",
    ),
)

registration_url = base_url + "/tickets" + '?search[sort]=reference&search[direction]=asc'
headers = {"Authorization": token, "Accept": "application/json"}

experiences = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}

# ticket release, last part of ticket url
exhibitors_tickets = os.getenv("EXHIBITORS", "").split(",")
speakers_tickets = os.getenv("SPEAKERS", "").split(",")
# create this file, list of speakers emails
try:
    from speakers import speakers
except ImportError:
    speakers = []


def get_tickets(event):
    """retrieves tickets from API and extract relevant data"""
    t_schema = TicketAPISchema()
    page = 1
    # while page is not None:
    while page < 2:
        log.debug("getting page %d", page)
        r = requests.get(
            f"https://api.tito.io/v3/{ACCOUNT}/{event}/tickets?page={page}&view=extended",
            headers=headers,
        ).json()
        data = t_schema.load(r)
        for ticket in data['tickets']:
            yield ticket
        page = data['meta']['next_page']


def get_lunches():
    r = requests.get(
        "https://api.tito.io/v3/python-ireland/pycon-limerick-2020/tickets.json?search[activity_ids]=1031346",
        headers=headers,
    )
    lunches = [ticket["reference"] for ticket in r.json()["tickets"]]
    return lunches


def get_delegates():
    r = requests.get(registration_url, headers=headers)
    lunch_refs = get_lunches()

    delegates = []
    for ticket in r.json()["tickets"]:
        email = ticket["email"]

        full_name = ticket["name"]
        reference = ticket["reference"]
        responses = ticket.get("responses")
        if responses is not None:
            experience = responses.get("your-python-experience")
            level = experiences.get(experience, 0)
        else:
            level = 0

        has_lunch = reference in lunch_refs

        ticket_class_url = ticket["relationships"]["release"]["links"]["related"]
        ticket_class_code = urlparse(ticket_class_url).path.split("/")[-1]
        exhibitor = ticket_class_code in exhibitors_tickets
        speaker = ticket_class_code in speakers_tickets
        # ticket_class_ = requests.get(ticket_class_url,
        #                              headers=headers).json()
        # ticket_class = ticket_class_['data']['attributes']['title']
        # exhibitor = 'exhibitor' in ticket_class.lower().split()

        first, rest = full_name.split(" ")[0], " ".join(full_name.split(" ")[1:])
        first = first.title()
        name = rest.title()
        try:
            delegates.append(
                Attendee(
                    first + " " + name[0] + ".",
                    full_name,
                    email,
                    reference,
                    level,
                    exhibitor,
                    speaker,
                    has_lunch,
                )
            )
        except IndexError:  # missing full name
            print(full_name, reference)

    return sorted(delegates, key=lambda x: x.reference)


from attendees import Attendee

if __name__ == "__main__":
    # as_of_now = get_delegates()
    as_of_now = [Attendee(ticket) for ticket in get_tickets(event)]
    pprint(as_of_now)


# Attendee = namedtuple(
#     "Attendee",
#     (
#         "display_name",
#         "full_name",
#         "email",
#         "reference",
#         "level",
#         "exhibitor",
#         "speaker",
#         "lunch",
#     ),
# )