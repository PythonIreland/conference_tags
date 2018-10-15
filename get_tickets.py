import requests
from pprint import pprint
from collections import namedtuple
from urllib.parse import urlparse

# Tito uses API keys to allow access to the API.
## You can find your API key by signing in at https://api.tito.io.

import os

auth_key = os.getenv('TITO_TOKEN')
token = "Token token={}".format(auth_key)
account = "python-ireland"
event = "pycon-ireland-2018"

base_url = 'https://api.tito.io/v2/{account}/{event}'.format(
    account=account,
    event=event,
)

Attendee = namedtuple('Attendee',
                      ('display_name', 'full_name',
                       'email', 'reference', 'level', 'exhibitor'))

registration_url = base_url + "/tickets"
headers = {'Authorization': token,
           'Accept': 'application / vnd.api + json'
           }

experiences = {
    'Beginner': 1,
    'Intermediate': 2,
    'Advanced': 3,
    'Expert': 4,
}

# ticket release, last part of ticket url
exhibitors_tickets = os.getenv('EXHIBITORS', '').split(',')


def get_delegates():
    r = requests.get(registration_url, headers=headers)
    delegates = []
    for registration in r.json()['data']:
        email = registration['attributes']['email']
        full_name = registration['attributes']['name']
        reference = registration['attributes']['reference']
        answers = registration.get('attributes', {}).get('answers')
        if answers is not None:
            experience = answers.get('your-python-experience')
            level = experiences.get(experience, 0)
        else:
            level = 0

        ticket_class_url = registration['relationships']['release']['links']['related']
        ticket_class_code = urlparse(ticket_class_url).path.split('/')[-1]
        exhibitor = ticket_class_code in exhibitors_tickets
        # ticket_class_ = requests.get(ticket_class_url,
        #                              headers=headers).json()
        # ticket_class = ticket_class_['data']['attributes']['title']
        # exhibitor = 'exhibitor' in ticket_class.lower().split()

        first, rest = full_name.split(' ')[0], ' '.join(full_name.split(' ')[1:])
        first = first.title()
        name = rest.title()
        try:
            delegates.append(Attendee(first + ' ' + name[0] + '.', full_name, email, reference, level, exhibitor))
        except IndexError:
            print(full_name, reference)

    return sorted(delegates, key=lambda x: x.reference)

# as_of_now = get_delegates()
# pprint(as_of_now)
