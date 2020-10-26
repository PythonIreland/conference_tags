import datetime
from attendees import Attendee


fake_data = sorted(
    [
        Attendee(
            {
                "name": "Nïçôlàys Laury",
                "responses": {
                    "your-python-experience": "Expert",
                },
                "last_name": "Laur",
                "reference": "OFXL-1",
                "first_name": "Nïçôlàys",
                "updated_at": datetime.datetime(
                    2020,
                    7,
                    7,
                    15,
                    10,
                    0,
                    tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
                ),
                "email": "someone@example.com",
            }
        ),
        Attendee(
            {
                "name": "Another Name",
                "responses": {
                    "your-python-experience": "Beginner",
                },
                "last_name": "Laur",
                "reference": "KBKQ-1",
                "first_name": "Avery long name",
                "updated_at": datetime.datetime(
                    2020,
                    5,
                    6,
                    12,
                    0,
                    0,
                    tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
                ),
                "email": "someone@example.com",
            }
        ),
    ],
    key=lambda x: x.reference,
)
