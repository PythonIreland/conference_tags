import datetime
import enum
import functools
import json
import os
import pathlib
import typing

import pandas as pd
import pytz
import reportlab.rl_config
import typer as typer
from pydantic import TypeAdapter
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import PCMYKColor, black, white
from reportlab.lib.pagesizes import A4, A5, landscape, portrait
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from alignment_guidelines import draw_guidelines, draw_margins
from config import settings
from get_tickets import get_tickets
from models import SpeakerModel, TicketModel
from utils import make_batches, two_per_page

here = os.path.dirname(__file__)
reportlab.rl_config.warnOnMissingFontGlyphs = 0


def register_fonts() -> None:
    """Register the TrueType fonts used for badge rendering.

    Loads the fonts configured in settings from the local ``fonts`` directory
    and registers them with ReportLab so they can be used when drawing text.

    Raises:
        FileNotFoundError: If any configured font file cannot be found.
        TTFError: If a font file cannot be parsed by ReportLab.
    """
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
    """Layout configuration and canvas holder for badge PDF generation.

    This encapsulates page size, margins, computed section sizes (recto/verso),
    and the ReportLab canvas onto which badges are drawn.

    Args:
        output_filename: Name of the output PDF file. If ``None``, a timestamped
            filename is generated unless ``settings.printout.debug`` is enabled,
            in which case ``tickets.pdf`` is used.

    Attributes:
        paper_size: The selected ReportLab page size (e.g., A4, A5).
        canvas: The ReportLab canvas used to draw the PDF.
        width: Page width in points.
        height: Page height in points.
        margin: Margin, in points.
        height_offset: Vertical translation applied when drawing halves.
        badge_per_sheet: Number of badges per sheet (depends on paper size).
        ordering_function: Function to enumerate/order tickets on the page.
        section_height: Height of a single badge section (recto/verso).
        section_width: Width of a single badge section (recto/verso).
    """

    def __init__(self, output_filename: str | None = None) -> None:
        if output_filename is None:
            if settings.printout.debug:
                output_filename = "tickets.pdf"
            else:
                timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
                output_filename = f"tickets-{timestamp}.pdf"

        self.paper_size = getattr(
            reportlab.lib.pagesizes,
            settings.printout.paper_size,
            A4,
        )
        if self.paper_size == A4:
            self.canvas = canvas.Canvas(
                output_filename,
                pagesize=portrait(A4),
            )
            self.width, self.height = A4
            self.margin = 0.5 * cm

            self.height_offset = self.height / 2.0 + self.margin
            self.badge_per_sheet = 2
            self.ordering_function = two_per_page
            self.section_height = self.height / 2.0 - self.margin

        elif self.paper_size == A5:
            self.canvas = canvas.Canvas(
                output_filename,
                pagesize=landscape(A5),
            )
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
    """Compute the font height in points for a given font face and size.

    Args:
        font_size: Requested font size in points.
        fontname: Registered ReportLab font name.

    Returns:
        The computed font height in points (ascent minus descent).
    """
    face = pdfmetrics.getFont(fontname).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (face.descent * font_size) / 1000.0
    height = ascent - descent  # <-- descent it's negative
    return height


def write_qr_code(delegate: TicketModel, layout) -> None:
    """Draw a QR code for the given attendee on the current section.

    The QR encodes "name <email>" and has the conference logo overlaid in the
    center to improve visual identity.

    Args:
        delegate: The attendee/ticket data used to populate the QR code.
        layout: The active layout/canvas context.
    """
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
    """Render the ticket reference number on the verso section.

    The reference is drawn once horizontally and once rotated near the fold
    line so it remains visible after cutting/folding.

    Args:
        ticket_reference: The ticket reference string to display.
        layout: The active layout/canvas context.
    """
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
    """Draw the ordering/index number for the ticket on the verso.

    Args:
        order_num: The ticket position/index to display.
        layout: The active layout/canvas context.
    """
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
    """Compose the verso: QR code, reference, and ordering number.

    Args:
        attendee: The attendee/ticket information.
        ticket_index: Position of the ticket in the current batch.
        layout: The active layout/canvas context.
    """
    write_qr_code(attendee, layout)
    # ticket num
    write_ticket_num(attendee.reference, layout)
    write_ordering_num(ticket_index, layout)


def write_recto(delegate: TicketModel, layout):
    """Compose the recto: background, title, logo, name, and role bar.

    Args:
        delegate: The attendee/ticket information.
        layout: The active layout/canvas context.
    """
    t = layout.canvas.beginText()
    t.setTextRenderMode(2)
    layout.canvas._code.append(t.getCode())

    # banner
    remove_width = 40
    banner_width = layout.section_width - remove_width
    banner_height = layout.section_height * 0.3333
    layout.canvas.drawImage(
        os.path.join(here, "img", settings.printout.background),
        remove_width // 2,
        layout.section_height - banner_height,
        width=banner_width,
        height=banner_height,
        preserveAspectRatio=True,
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
    # logo_width = 300 / 2
    # logo_height = 240 / 2
    logo_height = 960 * 0.5
    logo_width = 720 * 0.5
    # logo_width = logo_height = 110
    layout.canvas.drawImage(
        # os.path.join(here, "img", "tri-snakes_transparent_small_square.png"),
        os.path.join(here, "img", "tri-snake-jentic.png"),
        (layout.section_width - logo_width) / 2.0,
        (layout.section_height - logo_height) / 2.0 - 30,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=True,
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
    """Draw a thin border around the page for visual alignment checks.

    Args:
        layout: The active layout/canvas context.
    """
    layout.canvas.setDash(1, 0)
    # page border
    layout.canvas.line(0, 0, layout.width, 0)
    layout.canvas.line(0, 0, 0, layout.height)
    layout.canvas.line(0, layout.height, layout.width, layout.height)
    layout.canvas.line(layout.width, 0, layout.width, layout.height)


def draw_cutlines(layout):
    """Render cut and fold guides according to the selected paper size.

    Args:
        layout: The active layout/canvas context.
    """
    # halves
    if layout.paper_size == A4:
        layout.canvas.setDash(1, 0)
        layout.canvas.line(0, layout.height / 2.0, layout.width, layout.height / 2.0)
    # folding guide
    layout.canvas.setDash(3, 6)
    layout.canvas.line(layout.width / 2.0, 0, layout.width / 2.0, layout.height)

    layout.canvas.setDash(1, 0)


def create_badges(data, layout):
    """Build the full badge PDF for the provided ticket data.

    Iterates through tickets in page-sized batches, drawing verso and recto for
    each badge, and writes out the resulting PDF to ``layout.canvas``.

    Args:
        data: Iterable of ``TicketModel`` instances to render.
        layout: Configured ``LayoutParameters`` with an active canvas.
    """
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


def create_empty_badges(data, layout) -> None:
    """Build badges without verso (blank tickets) using the provided data.

    Args:
        data: Iterable of ``TicketModel`` (or placeholders) used only for recto.
        layout: Configured ``LayoutParameters`` with an active canvas.
    """
    for batch in make_batches(layout.ordering_function(data), layout.badge_per_sheet):
        if settings.printout.show_guidelines:
            draw_margins(layout)
            draw_guidelines(layout)

        draw_cutlines(layout)
        draw_page_borders(layout)

        layout.canvas.translate(0, layout.height_offset)
        for ticket_index, attendee in batch:
            layout.canvas.translate(layout.section_width, 0)
            write_recto(attendee, layout)
            layout.canvas.translate(-layout.section_width, -layout.height_offset)
        layout.canvas.showPage()  # finish the page, next statements should go next page
    layout.canvas.save()


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that serializes ``datetime`` objects as ISO-8601 strings."""

    def default(self, obj):
        if isinstance(obj, (datetime.datetime,)):
            return obj.isoformat()


app = typer.Typer()


def predicate_updated_from(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    """Return True if the ticket was updated on/after the given datetime.

    Args:
        ticket: Ticket to evaluate.
        when: Cutoff datetime (timezone-aware recommended).

    Returns:
        True if ``ticket.updated_at >= when``.
    """
    return ticket.updated_at >= when


def predicate_created_from(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    """Return True if the ticket was created on/after the given datetime.

    Args:
        ticket: Ticket to evaluate.
        when: Cutoff datetime (timezone-aware recommended).

    Returns:
        True if ``ticket.created_at >= when``.
    """
    return ticket.created_at >= when


def predicate_created_on(
    ticket: TicketModel,
    when: datetime.datetime,
) -> bool:
    """Return True if the ticket was created on the same calendar day.

    Args:
        ticket: Ticket to evaluate.
        when: Reference datetime.

    Returns:
        True if ``ticket.created_at.date() == when.date()``.
    """
    return ticket.created_at.date() == when.date()


def inject_speakers_in_tickets(
    tickets: list[TicketModel],
    speakers: list[SpeakerModel],
) -> list[TicketModel]:
    """Mark tickets as speakers/exhibitors based on metadata.

    A ticket is marked as a speaker if its email matches a provided speaker
    email. It is marked as exhibitor if the release title contains "exhibitor".

    Args:
        tickets: Original list of tickets.
        speakers: Known speakers (typically from Sessionize or similar).

    Returns:
        A new list of tickets with ``speaker`` and ``exhibitor`` flags updated.
    """
    local_speakers = {speaker.email for speaker in speakers}

    return [
        ticket.model_copy(
            update={
                "speaker": ticket.email in local_speakers,
                "exhibitor": "exhibitor" in ticket.release_title.lower(),
            }
        )
        for ticket in tickets
    ]


@app.command(name="build")
def cmd_build_new(
    ticket_files: typing.Annotated[list[pathlib.Path], typer.Argument()],
    speaker_files: typing.Annotated[
        list[pathlib.Path], typer.Option("--speakers", default_factory=list)
    ],
    output: typing.Annotated[pathlib.Path | None, typer.Option("--output")] = None,
    updated_from: typing.Annotated[
        datetime.datetime | None, typer.Option("--updated-from")
    ] = None,
    created_from: typing.Annotated[
        datetime.datetime | None, typer.Option("--created-from")
    ] = None,
    created_on: typing.Annotated[
        datetime.datetime | None, typer.Option("--created-on")
    ] = None,
    build: typing.Annotated[bool, typer.Option("--build/--no-build")] = True,
    fake_data: typing.Annotated[
        bool, typer.Option("--fake-data/--no-fake-data")
    ] = False,
    limit: typing.Annotated[int | None, typer.Option("--limit")] = None,
):
    """Build badges from ticket JSON files, with optional filtering.

    This is the primary command used to generate the badges PDF from one or more
    exported JSON files. Optionally merges speaker information, filters by
    creation/update dates, and can limit the number of badges.

    Args:
        ticket_files: One or more JSON files containing ``TicketModel`` entries.
        speaker_files: Optional JSON files containing ``SpeakerModel`` entries.
        output: Output PDF filename. If None, uses default naming.
        updated_from: Only include tickets updated on/after this datetime.
        created_from: Only include tickets created on/after this datetime.
        created_on: Only include tickets created on this calendar day.
        build: When True, generate the PDF; otherwise, only prepares data.
        fake_data: When True, use local fixture data instead of files.
        limit: If provided, limit the number of tickets processed.
    """
    if fake_data:
        from fixture_attendees import fake_data as tickets
    else:
        tickets = load_tickets(ticket_files)
        speakers = load_speakers(speaker_files)

        mapping_df: pd.DataFrame = pd.read_csv("emails.mapping.csv")
        mapping_df["tito_email"] = mapping_df["tito_email"].str.lower()
        mapping_df["sessionize_email"] = mapping_df["sessionize_email"].str.lower()

        for index, row in mapping_df.iterrows():
            for speaker in speakers:
                if speaker.email == row.sessionize_email:
                    # print(speaker, row)
                    speaker.email = row.tito_email

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

    # for ticket in sorted(tickets, key=lambda ticket: ticket.updated_at):
    #     print(
    #         ticket.reference,
    #         ticket.name,
    #         ticket.created_at.strftime("%Y-%m-%d"),
    #         ticket.updated_at.strftime("%Y-%m-%d"),
    #     )

    if build:
        if tickets:
            register_fonts()
            output_filename = str(output) if output else None
            layout = LayoutParameters(output_filename=output_filename)

            create_badges(
                sorted(tickets, key=lambda ticket: ticket.reference),
                layout,
            )
        else:
            print("Nothing to do")


def load_speakers(speaker_files: list[pathlib.Path]) -> list[SpeakerModel]:
    """Load and parse speakers from JSON files into ``SpeakerModel`` objects.

    Args:
        speaker_files: Paths to JSON files with arrays of speakers.

    Returns:
        A list of parsed ``SpeakerModel`` instances.
    """
    speakers: list[SpeakerModel] = []
    for speaker_file in speaker_files:
        speakers.extend(
            TypeAdapter(list[SpeakerModel]).validate_json(speaker_file.read_text())
        )
    return speakers


def load_tickets(ticket_files: list[pathlib.Path]) -> list[TicketModel]:
    """Load and parse tickets from JSON files into ``TicketModel`` objects.

    Args:
        ticket_files: Paths to JSON files with arrays of tickets.

    Returns:
        A list of parsed ``TicketModel`` instances.
    """
    tickets: list[TicketModel] = []
    for ticket_file in ticket_files:
        tickets.extend(
            TypeAdapter(list[TicketModel]).validate_json(ticket_file.read_text())
        )
    return tickets


@app.command(name="download-tickets")
def cmd_download_tickets(
    store_name: str = "tickets.json",
    event: str = settings.API.event,
):
    """Download tickets from the API and store them as pretty-printed JSON.

    Args:
        store_name: Output filename for the JSON payload.
        event: The event slug/identifier used by the API.
    """
    tickets: list[TicketModel] = list(get_tickets(event))
    with open(store_name, "w") as fp:
        json.dump(
            fp=fp,
            obj=[ticket.model_dump() for ticket in tickets],
            indent=4,
            cls=DateTimeEncoder,
        )
        print(f"{len(tickets)} tickets")


@app.command(name="missing-tickets-for-speakers")
def cmd_missing_tickets(
    ticket_files: list[pathlib.Path],
    speaker_files: list[pathlib.Path] = typer.Option([], "--speakers"),
):
    """Print speakers that do not have a corresponding attendee ticket.

    Args:
        ticket_files: JSON files with attendee tickets.
        speaker_files: JSON files with speakers.
    """
    tickets: list[TicketModel] = load_tickets(ticket_files=ticket_files)
    speakers: list[SpeakerModel] = load_speakers(speaker_files=speaker_files)

    unique_speakers = {
        speaker.email.lower(): speaker for speaker in speakers if speaker.email
    }
    unique_attendees = {ticket.email.lower() for ticket in tickets}

    diff_emails = set(unique_speakers.keys()) - unique_attendees

    for speaker_email in diff_emails:
        print(unique_speakers[speaker_email].name, speaker_email)


@app.command(name="print-reference")
def cmd_print_reference(
    ticket_files: list[pathlib.Path],
    reference: str,
    speaker_files: list[pathlib.Path] = typer.Option([], "--speakers"),
):
    """Build a badge PDF for a single ticket reference.

    Args:
        ticket_files: JSON files with attendee tickets.
        reference: Ticket reference to print.
        speaker_files: JSON files with speakers (to mark speakers/exhibitors).
    """
    tickets: list[TicketModel] = load_tickets(ticket_files=ticket_files)
    speakers: list[SpeakerModel] = load_speakers(speaker_files=speaker_files)
    tickets = inject_speakers_in_tickets(tickets, speakers)

    tickets = [ticket for ticket in tickets if ticket.reference == reference]
    # tickets.append(
    #     TicketModel.make_empty(exhibitor=False, speaker=False,)
    # )

    if tickets:
        register_fonts()
        layout = LayoutParameters()
        create_badges(tickets, layout)
    else:
        print("Nothing to do")


@app.command(name="blank-tickets")
def cmd_build_blank_tickets(
    limit: int = 5,
    exhibitor: bool = False,
    speaker: bool = False,
):
    """Generate a PDF with blank badges (no QR code).

    Args:
        limit: Number of blank tickets to generate.
        exhibitor: Whether badges should be labeled as exhibitor.
        speaker: Whether badges should be labeled as speaker.

    Raises:
        Exit: When both ``exhibitor`` and ``speaker`` are True.
    """
    if exhibitor and speaker:
        typer.echo("--exhibitor, --speaker are mutually exclusive")
        typer.Exit()

    register_fonts()
    layout = LayoutParameters(output_filename="blank-tickets.pdf")
    tickets = [
        TicketModel.make_empty(
            exhibitor=exhibitor,
            speaker=speaker,
        )
        for i in range(limit)
    ]
    create_empty_badges(tickets, layout)


class SpeakerEnum(str, enum.Enum):
    """Sorting options for speaker ticket listings."""

    NAME = "name"
    REFERENCE = "reference"


@app.command(name="speakers")
def cmd_print_speaker_tickets(
    ticket_files: list[pathlib.Path],
    speaker_files: list[pathlib.Path] = typer.Option([], "--speakers"),
    sort_by: SpeakerEnum = SpeakerEnum.NAME,
    build: bool = False,
) -> None:
    """List speaker tickets and optionally build a PDF for them.

    Args:
        ticket_files: JSON files with attendee tickets.
        speaker_files: JSON files with speakers.
        sort_by: Sort speakers by name or reference.
        build: When True, also render a PDF containing only speaker badges.
    """
    speakers: list[SpeakerModel] = load_speakers(speaker_files)

    tickets: list[TicketModel] = inject_speakers_in_tickets(
        load_tickets(ticket_files),
        speakers,
    )

    ticket_speakers = sorted(
        [ticket for ticket in tickets if ticket.speaker],
        key=lambda ticket: getattr(ticket, sort_by.value),
    )

    for ticket in ticket_speakers:
        print(ticket.reference, ticket.name)

    if build:
        register_fonts()
        layout = LayoutParameters()

        create_badges(ticket_speakers, layout)


if __name__ == "__main__":
    app()
