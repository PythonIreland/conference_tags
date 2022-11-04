import datetime

from models import TicketModel

fake_data = sorted(
    [
        TicketModel(
            name="Nïçôlàys Laury",
            responses={
                "python-experience": "Expert",
            },
            last_name="Laur",
            reference="OFXL-1",
            first_name="Nïçôlàys",
            created_at=datetime.datetime(
                2020,
                7,
                7,
                15,
                10,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
            ),
            updated_at=datetime.datetime(
                2020,
                7,
                7,
                15,
                10,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
            ),
            email="someone@example.com",
        ),
        TicketModel(
            name="Another Name",
            responses={
                "python-experience": "Beginner",
            },
            last_name="Laur",
            reference="KBKQ-1",
            first_name="Avery long name",
            created_at=datetime.datetime(
                2020,
                5,
                6,
                12,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
            ),
            updated_at=datetime.datetime(
                2020,
                5,
                6,
                12,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(0), "+0000"),
            ),
            email="someone@example.com",
        ),
    ],
    key=lambda x: x.reference,
)
