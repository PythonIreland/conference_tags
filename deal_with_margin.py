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

# set firring to None

reportlab.rl_config.warnOnMissingFontGlyphs = 0
pdfmetrics.registerFont(TTFont("ubuntu", "./fonts/UbuntuMono-R.ttf"))
pdfmetrics.registerFont(TTFont("Bree", "./fonts/BreeSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("BreeB", "./fonts/BreeBold.ttf"))

registerFontFamily(
    "Bree", normal="Bree", bold="BreeB", italic="Bree", boldItalic="BreeB"
)
registerFontFamily(
    "ubuntu", normal="ubuntu", bold="ubuntu", italic="ubuntu", boldItalic="ubuntu"
)

here = os.path.dirname(__file__)

irish_green = PCMYKColor(71, 0, 72, 40)
irish_orange = PCMYKColor(0, 43, 91, 0)

canvas = canvas.Canvas("margins.pdf", pagesize=A4)
width, height = A4
margin = .5 * cm
section_width = width / 2.0 - margin
section_height = height / 2.0 - margin


def make_batches(iterable, n):
    iterable = iter(iterable)
    n_rest = n - 1

    for item in iterable:
        rest = itertools.islice(iterable, n_rest)
        yield itertools.chain((item,), rest)


def draw_margins():
    # margins
    canvas.setDash(1, 4)
    # main
    canvas.setDash(1, 0)
    # canvas.line(page_margin_left, 0, page_margin_left, height)
    # canvas.line(width - page_margin_right, 0, width - page_margin_right, height)
    # canvas.line(0, page_margin_bottom, width, page_margin_bottom)
    # canvas.line(0, height - page_margin_top, width, height - page_margin_top)

    # page border
    canvas.line(0, 0, width, 0)
    canvas.line(0, 0, 0, height)
    canvas.line(0, height, width, height)
    canvas.line(width, 0, width, height)
    # halves
    canvas.line(0, height / 2.0, width, height / 2.0)
    canvas.line(width / 2.0, 0, width / 2.0, height)

    canvas.setDash(1, 4)
    canvas.line(width / 2.0 - margin, 0, width / 2.0 - margin, height)
    canvas.line(width / 2.0 + margin, 0, width / 2.0 + margin, height)
    canvas.line(0, height / 2.0 + margin, width, height / 2.0 + margin)
    canvas.line(0, height / 2.0 - margin, width, height / 2.0 - margin)


def write_qr_code(attendee, ticket_index):
    canvas.setStrokeColor(black)
    canvas.setFillColor(irish_green)
    canvas.rect(0, 0, section_width, section_height, fill=1, stroke=0)


def write_badge(attendee):
    canvas.setStrokeColor(black)
    canvas.setFillColor(irish_orange)
    canvas.rect(0, 0, section_width, section_height, fill=1, stroke=0)


def create_badges(data):
    # canvas.translate(0, section_height)

    for batch in make_batches(data, 2):

        # fold & cut helpers
        canvas.setDash(6, 3)
        canvas.line(width / 2.0, 0, width / 2.0, height)  # vertical line
        canvas.setDash(1, 0)
        canvas.line(0, height / 2.0, width, height / 2.0)  # horizontal
        canvas.setDash(1, 0)

        draw_margins()

        canvas.translate(0, height / 2.0 + margin)
        for pos, (ticket_index, attendee) in enumerate(batch, 1):
            write_qr_code(attendee, ticket_index)
            canvas.translate(width / 2.0 + margin, 0)
            write_badge(attendee)
            canvas.translate(-width / 2.0 - margin, -height / 2.0 - margin)
        canvas.showPage()  # finish the page, next statements should go next page
    canvas.save()


create_badges([(1, 2), (3, 4), (5, 6)])
