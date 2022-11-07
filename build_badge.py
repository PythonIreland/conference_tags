import datetime
import functools
import json
import os
import pathlib
import typing

import pydantic
import pytz
import reportlab.rl_config
import typer as typer
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import PCMYKColor
from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import A4, A5, portrait, landscape
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from alignment_guidelines import draw_guidelines, draw_margins
from config import settings
from get_tickets import get_tickets
from models import TicketModel, SpeakerModel
from utils import make_batches, two_per_page

here = os.path.dirname(__file__)
reportlab.rl_config.warnOnMissingFontGlyphs = 0


def register_fonts() -> None:
    pdfmetrics.registerFont(
        TTFont("reference", os.path.join(here, "fonts", settings.fonts.reference_font))
    )
    pdfmetrics.registerFont(
        TTFont(
            "conferenceFont",
            os.path.join(here, "fonts", settings.fonts.conference_font),
        )
    )
    pdfmetrics.registerFont(
        TTFont("nameFont", os.path.join(here, "fonts", settings.fonts.name_font))
    )


irish_green = PCMYKColor(71, 0, 72, 40)
irish_orange = PCMYKColor(0, 43, 91, 0)
banner_blue = PCMYKColor(98, 82, 0, 44)


class LayoutParameters:
    def __init__(self) -> None:
        if settings.printout.debug:
            output_filename = "tickets.pdf"
        else:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            output_filename = f"tickets-{timestamp}.pdf"

        self.paper_size = getattr(
            reportlab.lib.pagesizes, settings.printout.paper_size, A4
        )
        if self.paper_size == A4:
            self.canvas = canvas.Canvas(output_filename, pagesize=portrait(A4))
            self.width, self.height = A4
            self.margin = 0.5 * cm

            self.height_offset = self.height / 2.0 + self.margin
            self.badge_per_sheet = 2
            self.ordering_function = two_per_page
            self.section_height = self.height / 2.0 - self.margin

        elif self.paper_size == A5:
            self.canvas = canvas.Canvas(output_filename, pagesize=landscape(A5))
            self.width, self.height = landscape(A5)
            self.margin = 0
            self.height_offset = 0
            self.badge_per_sheet = 1
            self.ordering_function = enumerate
            self.section_height = self.height

        else:
            raise ValueError("what size is that?")

        # section means recto or verso
        self.section_width = self.width / 2.0 - self.margin


def get_font_size(font_size: int, fontname: str) -> int:
    face = pdfmetrics.getFont(fontname).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (face.descent * font_size) / 1000.0
    height = ascent - descent  # <-- descent it's negative
    return height


def write_qr_code(delegate: TicketModel, layout) -> None:
    qr_code = qr.QrCodeWidget(
        "{} <{}>".format(delegate.name, delegate.email), barLevel="H"
    )
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    qr_size = 200.0
    d = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0],
    )
    d.add(qr_code)
    renderPDF.draw(
        d,
        layout.canvas,
        (layout.section_width - qr_size) / 2.0,
        (layout.section_height - qr_size) / 2.0,
    )

    logo_width = 60
    logo_height = 60
    layout.canvas.drawImage(
        os.path.join(here, "img", "logo_in_qrcode.png"),
        (layout.section_width - logo_width) / 2.0,
        (layout.section_height - logo_height) / 2.0,
        width=logo_width,
        height=logo_height,
        mask="auto",
    )


def write_ticket_num(ticket_reference: str, layout) -> None:
    layout.canvas.saveState()

    t = layout.canvas.beginText()
    t.setTextRenderMode(2)
    layout.canvas._code.append(t.getCode())

    # ticket num
    layout.canvas.setStrokeColor(black)
    layout.canvas.setFillColor(black)
    layout.canvas.setLineWidth(0.5)

    font_size = 28
    layout.canvas.setFont("reference", font_size)
    text_w = stringWidth(ticket_reference, "reference", font_size)

    y_pos = layout.section_height - 20
    layout.canvas.drawString(0, y_pos, ticket_reference)
    # write again near fold line
    layout.canvas.rotate(-90)
    layout.canvas.drawString(-text_w, layout.section_width - 20, ticket_reference)
    layout.canvas.restoreState()


def write_ordering_num(order_num, layout):
    layout.canvas.saveState()
    t = layout.canvas.beginText()
    t.setTextRenderMode(2)
    layout.canvas._code.append(t.getCode())

    # ticket ordering index
    layout.canvas.setStrokeColor(black)
    layout.canvas.setFillColor(black)
    layout.canvas.setLineWidth(0.5)

    order_num = str(order_num)
    font_size = 28
    layout.canvas.setFont("reference", font_size)
    text_w = stringWidth(order_num, "reference", font_size)

    layout.canvas.drawString(
        layout.section_width - text_w, layout.section_height - 20, order_num
    )
    x_pos = -(layout.section_height + text_w) / 2.0
    layout.canvas.rotate(-90)
    layout.canvas.drawString(x_pos, layout.section_width - 20, order_num)
    layout.canvas.restoreState()


def write_verso(attendee: TicketModel, ticket_index: int, layout) -> None:
    write_qr_code(attendee, layout)
    # ticket num
    write_ticket_num(attendee.reference, layout)
    write_ordering_num(ticket_index, layout)


def write_recto(delegate: TicketModel, layout):
    t = layout.canvas.beginText()
    t.setTextRenderMode(2)
    layout.canvas._code.append(t.getCode())

    # banner
    banner_width = layout.section_width
    banner_height = layout.section_height * 0.3333
    layout.canvas.drawImage(
        os.path.join(here, "img", settings.printout.background),
        0,
        layout.section_height - banner_height,
        width=banner_width,
        height=banner_height,
        mask="auto",
    )

    # Conference name and year
    layout.canvas.setFont("conferenceFont", 32)
    layout.canvas.setStrokeColor(white)
    layout.canvas.setFillColor(irish_green)
    layout.canvas.setLineWidth(1.3)

    if settings.printout.include_title:
        event_title = settings.printout.title
        text_w = stringWidth(event_title, "conferenceFont", 32)
        x_pos = (layout.section_width - text_w) / 2
        layout.canvas.drawString(x_pos, layout.section_height - 64, event_title)

    # logo tri snake
    logo_width = logo_height = 110
    layout.canvas.drawImage(
        os.path.join(here, "img", "tri-snakes_transparent_small_square.png"),
        (layout.section_width - logo_width) / 2.0,
        (layout.section_height - logo_height)
        / 2.0,  # vertical offset of logo here is needed
        width=logo_width,
        height=logo_height,
        mask="auto",
    )

    # delegate name
    layout.canvas.setStrokeColor(black)
    layout.canvas.setFillColor(irish_green)
    layout.canvas.setLineWidth(0.7)

    font_size = 36
    fontname = "nameFont"

    layout.canvas.setFont(fontname, font_size)
    text_w = stringWidth(delegate.display_name, fontname, font_size)
    # resize as necessary to fit
    while text_w > layout.section_width:
        font_size -= 1
        layout.canvas.setFont(fontname, font_size)
        text_w = stringWidth(delegate.display_name, fontname, font_size)
    x_pos = (layout.section_width - text_w) / 2

    height = get_font_size(font_size, fontname)
    y_pos = layout.section_height * 0.25 - height / 4.0
    layout.canvas.drawString(x_pos, y_pos, delegate.display_name)

    # rectangle bottom
    border_thickness = layout.section_height / 6.0
    if delegate.exhibitor:
        layout.canvas.rect(
            0, 0, layout.section_width, border_thickness, fill=1, stroke=0
        )
        layout.canvas.setStrokeColor(black)
        layout.canvas.setFillColor(white)
        layout.canvas.setLineWidth(0.7)

        font_size = 32
        layout.canvas.setFont("nameFont", font_size)
        text_w = stringWidth("EXHIBITOR", "nameFont", font_size)
        x_pos = (layout.section_width - text_w) / 2
        layout.canvas.drawString(x_pos, 25, "EXHIBITOR")

    else:
        if delegate.speaker:
            layout.canvas.setFillColor(irish_orange)
        else:
            layout.canvas.setFillColor(banner_blue)
        layout.canvas.rect(
            0, 0, layout.section_width, border_thickness, fill=1, stroke=0
        )

        # level
        logo_width = logo_height = 30
        power_size = logo_width * delegate.level + 5 * (delegate.level - 1)
        power_start_x = (layout.section_width - power_size) / 2.0
        for i in range(delegate.level):
            layout.canvas.drawImage(
                os.path.join(here, "img", "Psf-Logo.png"),
                power_start_x + (logo_width + 5) * i,
                (layout.section_height / 6 - logo_height) / 2.0,
                width=logo_width,
                height=logo_height,
                mask="auto",
            )


def draw_page_borders(layout):
    layout.canvas.setDash(1, 0)
    # page border
    layout.canvas.line(0, 0, layout.width, 0)
    layout.canvas.line(0, 0, 0, layout.height)
    layout.canvas.line(0, layout.height, layout.width, layout.height)
    layout.canvas.line(layout.width, 0, layout.width, layout.height)


def draw_cutlines(layout):
    # halves
    if layout.paper_size == A4:
        layout.canvas.setDash(1, 0)
        layout.canvas.line(0, layout.height / 2.0, layout.width, layout.height / 2.0)
    # folding guide
    layout.canvas.setDash(3, 6)
    layout.canvas.line(layout.width / 2.0, 0, layout.width / 2.0, layout.height)

    layout.canvas.setDash(1, 0)


def create_badges(data, layout):
    for batch in make_batches(layout.ordering_function(data), layout.badge_per_sheet):

        if settings.printout.show_guidelines:
            draw_margins(layout)
            draw_guidelines(layout)

        draw_cutlines(layout)
        draw_page_borders(layout)

        layout.canvas.translate(0, layout.height_offset)
        for ticket_index, attendee in batch:
            write_verso(attendee, ticket_index, layout)
            layout.canvas.translate(layout.section_width, 0)
            write_recto(attendee, layout)
            layout.canvas.translate(-layout.section_width, -layout.height_offset)
        layout.canvas.showPage()  # finish the page, next statements should go next page
    layout.canvas.save()


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime,)):
            return obj.isoformat()


app = typer.Typer()


def predicate_updated_from(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    return ticket.updated_at >= when


def predicate_created_from(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    return ticket.created_at >= when


def predicate_created_on(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    return ticket.created_at.date() == when.date()


def inject_speakers_in_tickets(
    tickets: list[TicketModel],
    speakers: list[SpeakerModel],
) -> list[TicketModel]:
    local_speakers = {speaker.email for speaker in speakers}

    return [
        ticket.copy(
            update={
                "speaker": ticket.email in local_speakers,
                "exhibitor": "exhibitor" in ticket.release_title.lower(),
            }
        )
        for ticket in tickets
    ]


@app.command(name="build")
def cmd_build_new(
    ticket_files: typing.List[pathlib.Path],
    speaker_files: typing.List[pathlib.Path] = typer.Option([], "--speakers"),
    updated_from: typing.Optional[datetime.datetime] = typer.Option(
        None, "--updated-from"
    ),
    created_from: typing.Optional[datetime.datetime] = typer.Option(
        None, "--created-from"
    ),
    created_on: typing.Optional[datetime.datetime] = typer.Option(None, "--created-on"),
    build: bool = True,
    fake_data: bool = False,
    limit: typing.Optional[int] = None,
):
    if fake_data:
        from fixture_attendees import fake_data as tickets
    else:
        tickets = load_tickets(ticket_files)
        speakers = load_speakers(speaker_files)
        tickets = inject_speakers_in_tickets(tickets, speakers)

    if len(list(filter(None, [updated_from, created_from, created_on]))) > 1:
        typer.echo(
            "--updated-from, --created-from, --created-on are mutually exclusive"
        )
        typer.Exit()

    predicate = None
    timezone = pytz.timezone("Europe/Brussels")

    if updated_from:
        when = updated_from.astimezone(timezone)
        predicate = functools.partial(predicate_updated_from, when=when)

    if created_from:
        when = created_from.astimezone(timezone)
        predicate = functools.partial(predicate_created_from, when=when)

    if created_on:
        when = created_on.astimezone(timezone)
        predicate = functools.partial(predicate_created_on, when=when)

    if predicate:
        tickets = [ticket for ticket in tickets if predicate(ticket)]

    if isinstance(limit, int):
        tickets = tickets[:limit]

    for ticket in sorted(tickets, key=lambda ticket: ticket.updated_at):
        print(
            ticket.reference,
            ticket.name,
            ticket.created_at.strftime("%Y-%m-%d"),
            ticket.updated_at.strftime("%Y-%m-%d"),
        )

    if build:
        if tickets:
            register_fonts()
            layout = LayoutParameters()

            create_badges(
                sorted(tickets, key=lambda ticket: ticket.reference),
                layout,
            )
        else:
            print("Nothing to do")


def load_speakers(speaker_files: typing.List[pathlib.Path]) -> list[SpeakerModel]:
    speakers: list[SpeakerModel] = []
    for speaker_file in speaker_files:
        speakers.extend(pydantic.parse_file_as(list[SpeakerModel], speaker_file))
    return speakers


def load_tickets(ticket_files: typing.List[pathlib.Path]) -> list[TicketModel]:
    tickets: list[TicketModel] = []
    for ticket_file in ticket_files:
        tickets.extend(pydantic.parse_file_as(list[TicketModel], ticket_file))
    return tickets


@app.command(name="download-tickets")
def cmd_download_tickets(
    store_name: str = "tickets.json",
    event: str = settings.API.event,
):
    tickets: list[TicketModel] = list(get_tickets(event))
    with open(store_name, "w") as fp:
        json.dump(
            fp=fp,
            obj=[ticket.dict() for ticket in tickets],
            indent=4,
            cls=DateTimeEncoder,
        )
        print(f"{len(tickets)} tickets")


@app.command(name="missing-tickets-for-speakers")
def cmd_missing_tickets(
    ticket_files: typing.List[pathlib.Path],
    speaker_files: typing.List[pathlib.Path] = typer.Option([], "--speakers"),
):
    tickets: list[TicketModel] = load_tickets(ticket_files=ticket_files)
    speakers: list[SpeakerModel] = load_speakers(speaker_files=speaker_files)

    unique_speakers = {
        speaker.email.lower(): speaker for speaker in speakers if speaker.email
    }
    unique_attendees = {ticket.email.lower() for ticket in tickets}

    diff_emails = set(unique_speakers.keys()) - unique_attendees

    for speaker_email in diff_emails:
        print(unique_speakers[speaker_email].full_name, speaker_email)


@app.command(name="print-reference")
def cmd_print_reference(
    ticket_files: typing.List[pathlib.Path],
    reference: str,
    speaker_files: typing.List[pathlib.Path] = typer.Option([], "--speakers"),
):
    tickets: list[TicketModel] = load_tickets(ticket_files=ticket_files)
    speakers: list[SpeakerModel] = load_speakers(speaker_files=speaker_files)
    tickets = inject_speakers_in_tickets(tickets, speakers)

    tickets = [ticket for ticket in tickets if ticket.reference == reference]

    if tickets:
        register_fonts()
        layout = LayoutParameters()
        create_badges(tickets, layout)
    else:
        print("Nothing to do")


if __name__ == "__main__":
    app()
