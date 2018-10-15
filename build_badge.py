import itertools
import math
import os

import reportlab.rl_config
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import CMYKColor, PCMYKColor
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
page_margin_left = page_margin_right = page_margin_top = page_margin_bottom = .5 * cm
margin_left = margin_right = margin_top = margin_bottom = .5 * cm
section_write_width = section_width - margin_left
section_write_height = section_height - margin_top


def make_batches(iterable, n):
    iterable = iter(iterable)
    n_rest = n - 1

    for item in iterable:
        rest = itertools.islice(iterable, n_rest)
        yield itertools.chain((item,), rest)


def get_value(data):
    """ used to keep tickets ordering after page cut"""
    size = len(data)
    nb_pages = math.ceil(size / 2.0)
    for i in range(int(nb_pages)):
        yield (i, data[i])
        if i + nb_pages < size:
            yield (i + nb_pages, data[i + nb_pages])


def get_font_size(font_size, fontname):
    face = pdfmetrics.getFont(fontname).face
    ascent = (face.ascent * font_size) / 1000.0
    descent = (face.descent * font_size) / 1000.0
    height = ascent - descent  # <-- descent it's negative
    return height


def write_ticket_num(ticket_num, pos):
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
    x_pos = 2 * margin_left
    y_pos = section_height - 20 - (margin_top * pos)

    canvas.drawString(x_pos, y_pos, ticket_num)
    canvas.rotate(-90)
    canvas.drawString(-text_w - 2 * margin_bottom, section_width - 32, ticket_num)
    canvas.restoreState()


def write_qr_code(delegate, order_num, pos):
    """

    :param delegate: delegate object
    :param order_num: serial to ease manual ordering
    :param pos: top or bottom part of A4 (0=top)
    :return:
    """
    qr_code = qr.QrCodeWidget('{} <{}>'.format(
        delegate.full_name, delegate.email), barLevel='H')
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    qr_size = 200.0
    d = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    d.add(qr_code)
    local_section_height = section_height + margin_top * pos
    renderPDF.draw(d, canvas,
                   (section_width - margin_left - qr_size) / 2.0,
                   (local_section_height - qr_size) / 2.0)

    logo_width = 60
    logo_height = 60
    canvas.drawImage(os.path.join(here, "logo_in_qrcode_2.png"),
                     (section_width - margin_left - logo_width) / 2.0,
                     (local_section_height - logo_height) / 2.0,
                     width=logo_width, height=logo_height,
                     mask='auto')

    # ticket num
    write_ticket_num(delegate.reference, pos)

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

    canvas.drawString(section_width - margin_left - text_w,
                      section_height - 20 - (margin_top * pos), order_num)

    x_pos = -local_section_height + text_w + 2 * margin_top
    canvas.rotate(-90)
    canvas.drawString(x_pos+40, section_width - 32, order_num)
    canvas.restoreState()


def write_badge(delegate, pos):
    # TODO manage margins
    t = canvas.beginText()
    t.setTextRenderMode(2)
    canvas._code.append(t.getCode())

    # banner
    logo_width = section_write_width
    logo_height = section_write_height * .3333
    canvas.drawImage(
        os.path.join(here, "dublin_banner_2.jpg"),
        margin_left,
        (section_height - pos * margin_top - logo_height),
        # TODO will need to trim an horizontal slice from banner
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
    canvas.drawString(margin_left + x_pos, section_height - 55, python)

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
    fontname = 'Bree'

    canvas.setFont(fontname, font_size)
    text_w = stringWidth(delegate.display_name, 'Bree', font_size)
    # resize as necessary to fit
    while text_w > section_write_width:
        font_size -= 1
        canvas.setFont(fontname, font_size)
        text_w = stringWidth(delegate.display_name, 'Bree', font_size)
    x_pos = margin_left + (section_write_width - text_w) / 2

    height = get_font_size(font_size, fontname)

    y_pos = (0 if pos else margin_bottom) / 2.0 + section_height * .25 - height / 4.0

    canvas.drawString(x_pos, y_pos, delegate.display_name)

    speakers = [
        "speaker@example.ie"
    ]

    # rectangle bottom
    border_thickness = section_write_height / 6.0
    if delegate.exhibitor:
        canvas.rect(margin_left, margin_bottom,
                    section_write_width, border_thickness, fill=1, stroke=0)

        canvas.setStrokeColor(black)
        canvas.setFillColor(white)
        canvas.setLineWidth(0.7)

        font_size = 32
        canvas.setFont('Bree', font_size)
        text_w = stringWidth('EXHIBITOR', 'Bree', font_size)
        x_pos = margin_left + (section_write_width - text_w) / 2
        canvas.drawString(x_pos, 25 + margin_bottom, 'EXHIBITOR')

    else:
        if delegate.email in speakers:
            canvas.setFillColor(irish_orange)
        else:
            canvas.setFillColor(banner_blue)
        canvas.rect(margin_left, 0 if pos else margin_bottom,
                    section_write_width, border_thickness, fill=1, stroke=0)

        # level
        logo_width = logo_height = 30
        power_size = logo_width * delegate.level + 5 * (delegate.level - 1)
        power_start_x = (margin_left + section_width - power_size) / 2.0
        for i in range(delegate.level):
            canvas.drawImage(
                os.path.join(here, "Psf-Logo.png"),
                power_start_x + (logo_width + 5) * i,
                # (section_write_width - logo_width) / 2.0,
                (0 if pos else margin_bottom) + (border_thickness - logo_height) / 2.0,
                width=logo_width, height=logo_height,
                mask='auto')


def draw_guidelines():
    # horizontals
    canvas.setDash(1, 8)
    canvas.line(0, section_height * .125, width, section_height * .125)
    canvas.line(0, section_height * .25, width, section_height * .25)
    canvas.line(0, section_height * .5, width, section_height * .5)
    canvas.line(0, section_height * .75, width, section_height * .75)
    canvas.line(0, section_height * .875, width, section_height * .875)
    canvas.setDash(2, 2)
    canvas.line(0, margin_bottom + section_write_height / 6.0,
                width, margin_bottom + section_write_height / 6.0)  # horizontal
    canvas.line(0, section_height * .3333, width, section_height * .3333)  # horizontal
    canvas.line(0, margin_bottom + section_write_height * .6666, width,
                margin_bottom + section_write_height * .6666)  # horizontal

    canvas.setDash(1, 0)


def draw_margins():
    canvas.setDash(1, 0)
    # page border
    canvas.line(0, 0, width, 0)
    canvas.line(0, 0, 0, height)
    canvas.line(0, height, width, height)
    canvas.line(width, 0, width, height)

    canvas.setDash(1, 4)
    canvas.line(width / 2.0 - margin_right, 0, width / 2.0 - margin_right, height)
    canvas.line(width / 2.0 + margin_left, 0, width / 2.0 + margin_left, height)
    canvas.line(0, height / 2.0 + margin_bottom, width, height / 2.0 + margin_bottom)
    canvas.line(0, height / 2.0 - margin_top, width, height / 2.0 - margin_top)

    canvas.setDash(1, 0)


def draw_cutlines():
    # halves
    canvas.setDash(1, 0)
    canvas.line(0, height / 2.0, width, height / 2.0)
    canvas.setDash(3, 6)

    canvas.line(width / 2.0, 0, width / 2.0, height)
    canvas.setDash(1, 0)


def create_badges(data):
    # 2 per page, targeting A4
    for batch in make_batches(get_value(data), 2):

        # fold & cut helpers
        canvas.setDash(6, 3)
        canvas.line(section_width, 0, section_width, height)  # vertical line
        canvas.setDash(1, 0)
        canvas.line(0, section_height, width, section_height)  # horizontal

        canvas.setDash(1, 0)

        # draw_margins()
        draw_cutlines()
        # draw_guidelines()

        canvas.translate(0, height / 2.0)
        for pos, (ticket_index, attendee) in enumerate(batch):
            write_qr_code(attendee, ticket_index, pos % 2)
            canvas.translate(width / 2.0, 0)
            write_badge(attendee, pos % 2)
            canvas.translate(-width / 2.0, -height / 2.0)
        canvas.showPage()  # finish the page, next statements should go next page
    canvas.save()


data = sorted([
    Attendee('Nïçôlàs L.', 'Nïçôlàs ', 'test@example.ie', '1IO0-1', 0, True),
    Attendee('Ipsum L.', 'Lorem ', 'test@example.ie', 'ABCD', 1, False),
    Attendee('Lorem L.', 'Nicolas ', 'speaker@example.ie', 'KSDF', 2, False),
    Attendee('Vishal V.', 'doomsday', 'mad_devop@example.ie', 'OPPP-1', 7, False),
    # Attendee('Sic amen L.', 'Nicolas ', 'organizer@example.ie', 'OPPP-1', 3, False),
    # Attendee('Nijwcolas L.', 'Nicolas ', 'test@example.ie', 'Z2B8-2', 4, False),
    # Attendee('Dolor L.', 'Nicolas ', 'test@example.ie', 'ZWWX-1', 0, False),
], key=lambda x: x.reference)

create_badges(data)
