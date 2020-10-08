import datetime
from pprint import pprint

from sqlalchemy import Table, MetaData, Column, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker

from attendees import Attendee
from config import settings

metadata = MetaData()

engine = create_engine(settings.database.conn_string,
                       echo=settings.database.echo)

attendee = Table(
    "attendees",
    metadata,
    Column("reference", String(7), primary_key=True),
    Column("name", String(128)),
    Column("updated_at", DateTime(), default=datetime.datetime.utcnow),
)

mapper(Attendee, attendee)

# metadata.drop_all(bind=engine)
metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()


def filter_new_records(data):
    res_as_dict = {
        delegate.reference: delegate.updated_at.replace(tzinfo=datetime.timezone.utc)
        for delegate in session.query(Attendee.reference, Attendee.updated_at).all()
    }

    new_records = [
        delegate for delegate in data
        if delegate.reference not in res_as_dict
    ]
    updated_records = [
        delegate for delegate in data
        if (delegate.reference in res_as_dict)
           and res_as_dict[delegate.reference] < delegate.updated_at
    ]
    if updated_records:
        stmt = (
            attendee.delete()
                .where(Attendee.reference.in_(
                [r.reference for r in updated_records]
            )))
        session.execute(stmt)
        session.commit()
        session.add_all(updated_records)
        session.commit()

    if new_records:
        session.add_all(new_records)
        session.commit()

    return sorted(new_records + updated_records, key=lambda x: x.reference)


if __name__ == "__main__":
    from fixture_attendees import fake_data

    new_data = filter_new_records(fake_data)
    pprint(new_data)
