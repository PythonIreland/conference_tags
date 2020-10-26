import datetime
import os

import reportlab.rl_config
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
from attendees import Attendee
from repos import filter_new_records
from config import settings
from get_tickets import get_tickets
from utils import make_batches, two_per_page

here = os.path.dirname(__file__)
reportlab.rl_config.warnOnMissingFontGlyphs = 0


def register_fonts():
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
    def __init__(self):
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


def get_font_size(font_size, fontname):
    face = pdfmetrics.getFont(fontname).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (face.descent * font_size) / 1000.0
    height = ascent - descent  # <-- descent it's negative
    return height


def write_qr_code(delegate, layout):
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


def write_ticket_num(ticket_num, layout):
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
    text_w = stringWidth(ticket_num, "reference", font_size)

    y_pos = layout.section_height - 20
    layout.canvas.drawString(0, y_pos, ticket_num)
    # write again near fold line
    layout.canvas.rotate(-90)
    layout.canvas.drawString(-text_w, layout.section_width - 20, ticket_num)
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


def write_verso(attendee, ticket_index, layout):
    write_qr_code(attendee, layout)
    # ticket num
    write_ticket_num(attendee.reference, layout)
    write_ordering_num(ticket_index, layout)


def write_recto(delegate, layout):
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


if __name__ == "__main__":
    register_fonts()
    layout = LayoutParameters()
    # data = [ticket for ticket in get_tickets(settings.API.event)]
    # data = filter_new_records(data)
    from fixture_attendees import fake_data as data

    if data:
        create_badges(data, layout)
    else:
        print("Nothing to do")
