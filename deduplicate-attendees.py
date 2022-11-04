import collections
import json

import pydantic
from openpyxl.workbook import Workbook

from models import TicketModel


def main():
    years = [2015, 2016, 2017, 2018, 2019, 2022]
    ticket_files = [
        (year, pydantic.parse_file_as(list[TicketModel], f"tickets-{year}.json"))
        for year in years
    ]

    attendees = collections.defaultdict(lambda: {"name": "", "years": []})

    for (year, tickets) in ticket_files:
        for ticket in tickets:
            if not ticket.email:
                continue
            attendees[ticket.email]["name"] = ticket.name
            attendees[ticket.email]["years"].append(year)

    # sorted_emails = sorted(attendees.keys())
    with open("sorted_attendees.json", "w") as fp:
        json.dump(
            fp=fp,
            obj=[
                {
                    "email": email,
                    "name": attendees[email]["name"],
                    "years": attendees[email]["years"],
                }
                for email in sorted(attendees.keys())
            ],
            indent=4,
        )

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Attendees"
    ws1.append(["Email", "Name", "Years"])

    for index, email in enumerate(sorted(attendees.keys()), 1):
        ws1.append(
            [
                email,
                attendees[email]["name"],
                ",".join(map(str, attendees[email]["years"])),
            ],
        )
    wb.save("attendees.xlsx")


if __name__ == "__main__":
    main()
