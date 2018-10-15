from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import reportlab.rl_config
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import CMYKColor, PCMYKColor
import os
import itertools
from reportlab.graphics.barcode import qr

from reportlab.lib.colors import Color, black, blue, red, green, white, transparent

from get_tickets import Attendee
from get_tickets import get_delegates

reportlab.rl_config.warnOnMissingFontGlyphs = 0
pdfmetrics.registerFont(TTFont('ubuntu', './fonts/UbuntuMono-R.ttf'))
pdfmetrics.registerFont(TTFont('Bree', './fonts/BreeSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('BreeB', './fonts/BreeBold.ttf'))

registerFontFamily('Bree', normal='Bree', bold='BreeB', italic='Bree', boldItalic='BreeB')
registerFontFamily('ubuntu', normal='ubuntu', bold='ubuntu', italic='ubuntu', boldItalic='ubuntu')


here = os.path.dirname(__file__)

irish_green = PCMYKColor(71, 0, 72, 40)
irish_orange = PCMYKColor(0, 43, 91, 0)
banner_blue = PCMYKColor(98, 82, 0, 44)

canvas = canvas.Canvas('tickets.pdf', pagesize=A4)
width, height = A4

section_width = width / 2.0
section_height = height / 2.0

margin_left = margin_right = 5
section_write_width = (width - margin_left - margin_right) / 2.0


def make_batches(iterable, n):
    iterable = iter(iterable)
    n_rest = n - 1

    for item in iterable:
        rest = itertools.islice(iterable, n_rest)
        yield itertools.chain((item,), rest)


def write_ticket_num(ticket_num):
    canvas.saveState()

    t = canvas.beginText()
    t.setTextRenderMode(2)
    canvas._code.append(t.getCode())

    # ticket num
    canvas.setStrokeColor(black)
    canvas.setFillColor(black)
    canvas.setLineWidth(0.5)

    font_size = 28
    canvas.setFont('ubuntu', font_size)
    text_w = stringWidth(ticket_num, 'ubuntu', font_size)
    x_pos = section_write_width - text_w - margin_right
    canvas.drawString(x_pos, section_height - 30, ticket_num)
    canvas.rotate(90)
    canvas.drawString(section_height - text_w - margin_right - 5, -30, ticket_num)
    canvas.restoreState()


def write_qr_code(name, email, ticket_num, order_num):
    qr_code = qr.QrCodeWidget('{} <{}>'.format(name, email), barLevel='H')
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    qr_size = 200.0
    d = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, canvas, (section_width - qr_size) / 2.0, (section_height - qr_size) / 2.0)

    logo_width = 60
    logo_height = 60
    canvas.drawImage(os.path.join(here, "logo_in_qrcode_2.png"),
                     (section_write_width - logo_width) / 2.0,
                     (section_height - logo_height) / 2.0,
                     width=logo_width, height=logo_height,
                     mask='auto')

    # ticket num
    write_ticket_num(ticket_num)

    canvas.saveState()

    t = canvas.beginText()
    t.setTextRenderMode(2)
    canvas._code.append(t.getCode())

    # ticket ordering index
    canvas.setStrokeColor(black)
    canvas.setFillColor(black)
    canvas.setLineWidth(0.5)

    order_num = str(order_num)
    font_size = 28
    canvas.setFont('ubuntu', font_size)
    text_w = stringWidth(order_num, 'ubuntu', font_size)
    x_pos = section_write_width - text_w - margin_right
    canvas.rotate(90)
    canvas.drawString(2 * margin_left, -30, order_num)
    canvas.restoreState()


# canvas.line(margin_left, 0, margin_left, section_height)  # left margin
# canvas.line(section_width - margin_right, 0, section_width - margin_right, section_height)  # right line

# todo refactor pass delegate
def write_badge(name, level, exhibitor, email):
    t = canvas.beginText()
    t.setTextRenderMode(2)
    canvas._code.append(t.getCode())

    # banner
    logo_width = section_width
    logo_height = 140
    canvas.drawImage(
        os.path.join(here, "dublin_banner_2.jpg"),
        0,
        (section_height - logo_height),
        width=logo_width, height=logo_height,
        mask='auto')

    # Conference name and year
    canvas.setFont('BreeB', 32)
    canvas.setStrokeColor(white)
    canvas.setFillColor(irish_green)
    canvas.setLineWidth(1.3)

    python = "Pycon Ireland 2018"
    text_w = stringWidth(python, 'BreeB', 32)
    x_pos = (section_write_width - text_w) / 2
    canvas.drawString(x_pos, section_height - 60, python)

    # logo
    logo_width = logo_height = 110
    canvas.drawImage(
        os.path.join(here, "logo4.png"),
        (section_write_width - logo_width) / 2.0,
        (section_height - logo_height) / 2.0,  # vertical offset of logo here is needed
        width=logo_width, height=logo_height,
        mask='auto')

    # name
    canvas.setStrokeColor(black)
    canvas.setFillColor(irish_green)
    canvas.setLineWidth(0.7)

    font_size = 32
    canvas.setFont('Bree', font_size)
    text_w = stringWidth(name, 'Bree', font_size)
    # resize as necessary to fit
    while text_w > section_write_width:
        font_size -= 1
        canvas.setFont('Bree', font_size)
        text_w = stringWidth(name, 'Bree', font_size)
    x_pos = (section_write_width - text_w) / 2

    fontname = 'Bree'
    face = pdfmetrics.getFont(fontname).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (face.descent * font_size) / 1000.0
    height = ascent - descent  # <-- descent it's negative
    y_pos = section_height / 4.0 - height / 4.0

    canvas.drawString(x_pos, y_pos, name)

    speakers = [
        "speaker@example.ie"
    ]

    # rectangle bottom
    border_thickness = section_height * .1666
    if exhibitor:
        canvas.rect(0, 0, section_width, border_thickness, fill=1, stroke=0)

        canvas.setStrokeColor(black)
        canvas.setFillColor(white)
        canvas.setLineWidth(0.7)

        font_size = 32
        canvas.setFont('Bree', font_size)
        text_w = stringWidth('EXHIBITOR', 'Bree', font_size)
        x_pos = (section_write_width - text_w) / 2
        canvas.drawString(x_pos, 25, 'EXHIBITOR')

    else:
        if email in speakers:
            canvas.setFillColor(irish_orange)
            # canvas.setFillColorRGB(255 / 255.0, 89 / 255.0, 19 / 255.0)
        else:
            canvas.setFillColor(banner_blue)
            # canvas.setFillColorRGB(9 / 255.0, 11 / 255.0, 68 / 255.0)
        canvas.rect(0, 0, section_width, border_thickness, fill=1, stroke=0)

        # level
        logo_width = logo_height = 30
        power_size = logo_width * level + 5 * (level - 1)
        power_start_x = (section_write_width - power_size) / 2.0
        for i in range(level):
            canvas.drawImage(
                os.path.join(here, "Psf-Logo.png"),
                power_start_x + (logo_width + 5) * i,
                # (section_write_width - logo_width) / 2.0,
                (border_thickness - logo_height) / 2.0,
                width=logo_width, height=logo_height,
                mask='auto')


import math


def get_value(data):
    size = len(data)
    nb_pages = math.ceil(size / 2.0)
    for i in range(int(nb_pages)):
        yield (i, data[i])
        if i + nb_pages < size:
            yield (i + nb_pages, data[i + nb_pages])


def create_badges(data):
    # canvas.translate(0, section_height)

    for batch in make_batches(get_value(data), 2):

        # fold & cut helpers
        canvas.setDash(6, 3)
        canvas.line(section_width, 0, section_width, height)  # vertical line
        canvas.setDash(1, 0)
        canvas.line(0, section_height, width, section_height)  # horizontal

        # guide, delete
        # canvas.setDash(1, 4)
        # canvas.line(0, section_height*.125, width, section_height*.125)  # horizontal
        # canvas.line(0, section_height*.25, width, section_height*.25)  # horizontal
        # canvas.line(0, section_height*.5, width, section_height*.5)  # horizontal
        # canvas.line(0, section_height*.75, width, section_height*.75)  # horizontal
        # canvas.line(0, section_height*.875, width, section_height*.875)  # horizontal
        # canvas.setDash(1, 0)
        #
        # canvas.setDash(2, 2)
        # canvas.line(0, section_height*.1666, width, section_height*.1666)  # horizontal
        # canvas.line(0, section_height*.3333, width, section_height*.3333)  # horizontal
        # canvas.line(0, section_height*.5, width, section_height*.5)  # horizontal
        # canvas.line(0, section_height*.6666, width, section_height*.6666)  # horizontal

        canvas.setDash(1, 0)

        canvas.translate(0, section_height)
        for ticket_index, attendee in batch:
            write_qr_code(attendee.full_name, attendee.email, attendee.reference, ticket_index)
            canvas.translate(section_width, 0)
            write_badge(attendee.display_name, attendee.level, attendee.exhibitor, attendee.email)
            canvas.translate(-section_width, -section_height)
        canvas.showPage()  # finish the page, next statements should go next page
    canvas.save()


data = sorted([
    Attendee('Nïçôlàs L.', 'Nïçôlàs ', 'test@example.ie', '1IO0-1', 0, True),
    Attendee('Ipsum L.', 'Lorem ', 'test@example.ie', 'ABCD', 1, False),
    Attendee('Lorem L.', 'Nicolas ', 'speaker@example.ie', 'KSDF', 2, False),
    Attendee('Sic amen L.', 'Nicolas ', 'organizer@example.ie', 'OPPP-1', 3, False),
    Attendee('Nijwcolas L.', 'Nicolas ', 'test@example.ie', 'Z2B8-2', 4, False),
    Attendee('Dolor L.', 'Nicolas ', 'test@example.ie', 'ZWWX-1', 0, False),
], key=lambda x: x.reference)

create_badges(data)
