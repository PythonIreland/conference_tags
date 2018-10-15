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

# data = get_delegates()

# data = [
#     Attendee(display_name='Vishal V.', full_name='Vishal Vatsa', email='vishal.vatsa@gmail.com', reference='SFPH-1',
#              level=3, exhibitor=False),
#
#     Attendee(display_name='Hans C.', full_name='Hans Chan', email='hanschan13@gmail.com', reference='6U0R-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='John K.', full_name='John Kee', email='jchkee@gmail.com', reference='73QB-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Olwyn L.', full_name='Olwyn Lee', email='olwynlee@gmail.com', reference='7A4J-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Diego M.', full_name='Diego Menin', email='dmenin@gmail.com', reference='7KFN-1', level=4,
#              exhibitor=False),
#     Attendee(display_name='Roman G.', full_name='Roman Golovnya', email='x14126575@student.ncirl.ie',
#              reference='8TJK-1', level=3, exhibitor=False),
#     Attendee(display_name='Stefano M.', full_name='Stefano Mauceri', email='stefano.mauceri@ucdconnect.ie',
#              reference='986N-1', level=3, exhibitor=False),
#     Attendee(display_name='Benjamin R.', full_name='Benjamin Roques', email='oxis44@gmail.com', reference='9ZJV-2',
#              level=2, exhibitor=False),
#     Attendee(display_name='Shivam A.', full_name='Shivam Agarwal', email='shivam.agarwal@ucdconnect.ie',
#              reference='ABGP-1', level=2, exhibitor=False),
#     Attendee(display_name='John D.', full_name='John Doherty', email='sean.doherty1@gmail.com', reference='AEUV-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Vincent G.', full_name='Vincent Gilcreest', email='vgilcreest@gmail.com', reference='AFOF-1',
#              level=0, exhibitor=False),
#     Attendee(display_name='Ugo T.', full_name='Ugo Tarrade', email='ugo.tarrade@gmail.com', reference='AOH2-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Julie P.', full_name='Julie Pichon', email='julie.pichon@gmail.com', reference='APG4-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Fouad S.', full_name='Fouad Shammary', email='fouad89ahmed@gmail.com', reference='AQ0D-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Aurelia P.', full_name='Aurelia Power', email='aurelia.power@itb.ie', reference='ASE8-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Joanne D.', full_name='Joanne Dennehy', email='fractal.rainbow@gmail.com',
#              reference='AUWG-1', level=3, exhibitor=False),
#     Attendee(display_name='Nicolas L.', full_name='Nicolas Laurance', email='nicolas.laurance@gmail.com',
#              reference='AYEY-1', level=0, exhibitor=False),
#     Attendee(display_name='Piotr J.', full_name='Piotr Jedrys', email='zrebie@gmail.com', reference='AYGL-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Ancil C.', full_name='Ancil Crayton', email='ancil.crayton@ucdconnect.ie',
#              reference='BAUO-1', level=3, exhibitor=False),
#     Attendee(display_name='Gail M.', full_name='Gail Melia', email='gail.melia@gmail.com', reference='BDMB-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Patrick C.', full_name='Patrick Claffey', email='patclaffey@gmail.com', reference='BE1E-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Peter M.', full_name='Peter Morgan', email='peter.morgan@python.ie', reference='BE83-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Colette C.', full_name='Colette Condon', email='colettecondon@gmail.com', reference='BEMR-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Neal Ó.', full_name='Neal Ó Riain', email='oriainn@tcd.ie', reference='BEYI-1', level=4,
#              exhibitor=False),
#     Attendee(display_name='Ewa M.', full_name='Ewa Modrzejewska', email='aweelka@gmail.com', reference='BGKZ-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Kevin G.', full_name='Kevin Gill', email='kevin@movieextras.ie', reference='CCTT-1', level=4,
#              exhibitor=False),
#     Attendee(display_name='David D.', full_name='David Dolan', email='daithidolan@gmail.com', reference='CEVQ-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Julie R.', full_name='Julie Regan', email='julieregan7@gmail.com', reference='CIHR-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='David M.', full_name='David Murrells', email='davemurrells@gmail.com', reference='CQKM-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Evan B.', full_name='Evan Brady', email='evan@knowyournumbers.ie', reference='DBWX-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Ana B.', full_name='Ana Borreguero', email='ana_m_borreguero@yahoo.com', reference='DIX5-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Gunnar V.', full_name='Gunnar Voss', email='gvoss@blizzard.com', reference='DKND-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Neil K.', full_name='Neil Kenealy', email='neilkenealy@gmail.com', reference='DKTP-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Ulrich P.', full_name='Ulrich Petri', email='pyconie@ulo.pe', reference='DLWG-1', level=4,
#              exhibitor=False),
#     Attendee(display_name='Jose M.', full_name='Jose Manuel Ortega', email='jmoc25@gmail.com', reference='DTO3-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Nina H.', full_name='Nina Hagemann', email='nina.n.hagemann@googlemail.com',
#              reference='DURJ-1', level=2, exhibitor=False),
#     Attendee(display_name='Michele D.', full_name='Michele De Simoni', email='ubik@ubik.tech', reference='EBAO-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Vivek R.', full_name='Vivek Rawat', email='vivekrawat08@gmail.com', reference='EH3S-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Maura W.', full_name='Maura Walsh', email='mwalsh029@gmail.com', reference='EHGW-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Pritam P.', full_name='Pritam Pan', email='pritam_tict@hotmail.com', reference='EIAQ-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Lucas D.', full_name='Lucas Durand', email='lucas.durand@gmail.com', reference='EIDG-1',
#              level=4, exhibitor=False),
#     Attendee(display_name='Jernej H.', full_name='Jernej Hribar', email='jhribar@tcd.ie', reference='EIL8-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Shane L.', full_name='Shane Lynn', email='shane@edgetier.com', reference='ESW6-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Michael N.', full_name='Michael Niland', email='niland.michael.j@gmail.com',
#              reference='ESXR-1', level=1, exhibitor=False),
#     Attendee(display_name='Andrew B.', full_name='Andrew Bolster', email='me@andrewbolster.info', reference='EVDB-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='John D.', full_name='John Dwan', email='dwanjohn@yahoo.ie', reference='F1FR-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='John H.', full_name='John Harrington', email='johnharr.ie@gmail.com', reference='FE2F-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Stephen O.', full_name='Stephen Oman', email='stephen.oman@yahoo.co.uk', reference='FV8W-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Can E.', full_name='Can Eldem', email='eldemcan@gmail.com', reference='GDSG-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Stephen N.', full_name='Stephen Naughton', email='stephennaughton@yahoo.com',
#              reference='HAK2-1', level=2, exhibitor=False),
#     Attendee(display_name='Frank H.', full_name='Frank Humphreys', email='Frank.Humphreys@gmail.com',
#              reference='HDLN-1', level=2, exhibitor=False),
#     Attendee(display_name='Diogo P.', full_name='Diogo Pessoa', email='diogo.santos.pessoa@gmail.com',
#              reference='HKVM-1', level=2, exhibitor=False),
#     Attendee(display_name='Sofiia K.', full_name='Sofiia Kosovan', email='sofiia.kosovan@gmail.com', reference='I5DF-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Linda B.', full_name='Linda Browne', email='lcopy@hotmail.co.uk', reference='I5JL-1',
#              level=0, exhibitor=False),
#     Attendee(display_name='Miguel C.', full_name='Miguel Carrera', email='miguel.tpy@gmail.com', reference='IEIW-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Stephen M.', full_name='Stephen Murphy', email='president.cstai@gmail.com',
#              reference='IEQK-1', level=2, exhibitor=False),
#     Attendee(display_name='Imran K.', full_name='Imran Khan', email='imrankhan17@hotmail.co.uk', reference='IG8U-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Fergal W.', full_name='Fergal Walsh', email='fergal@hipolabs.com', reference='INGY-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Usman G.', full_name='Usman Ghani', email='usman_gujar@yahoo.com', reference='IXBD-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Brian L.', full_name='Brian Lynch', email='bglynch17@gmail.com', reference='JCX7-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Michael K.', full_name='Michael King', email='michael.king@fijowave.com', reference='JDH5-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Christopher M.', full_name='Christopher Mahon', email='christopher.mahon@fijowave.com',
#              reference='JDH5-2', level=3, exhibitor=False),
#     Attendee(display_name='Nils O.', full_name='Nils Olofsson', email='nils@olofsson.tv', reference='JDKB-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Matthew M.', full_name='Matthew McKenna', email='mattheweb.mckenna+pyconie18@gmail.com',
#              reference='JDRH-1', level=2, exhibitor=False),
#     Attendee(display_name='Krzysztof D.', full_name='Krzysztof Dajka', email='krisdajka@gmail.com', reference='JF5R-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Kevin O.', full_name="Kevin O'Brien", email='kevin.obrien@python.ie', reference='JJQ6-1',
#              level=4, exhibitor=False),
#     Attendee(display_name='Ronan H.', full_name='Ronan Hayes', email='ronan@batmansdad.com', reference='K5YD-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Marcin S.', full_name='Marcin Stepien', email='Marcin.Stepien@outlook.com',
#              reference='KCBJ-1', level=1, exhibitor=False),
#     Attendee(display_name='André M.', full_name='André Miguel Dias Claro', email='andre.claro@gmail.com',
#              reference='KJAP-1', level=2, exhibitor=False),
#     Attendee(display_name='Olga L.', full_name='Olga Lyashevska', email='purchasing@gmit.ie', reference='KPFW-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Jolene D.', full_name='Jolene Dunne', email='jolene.dunne@gmail.com', reference='KR1H-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='David M.', full_name='David Mcilwee', email='blak631@gmail.com', reference='LHFN-1', level=4,
#              exhibitor=False),
#     Attendee(display_name='Pedro A.', full_name='Pedro Araujo', email='pedro@riffstation.com', reference='LRN4-1',
#              level=0, exhibitor=False),
#     Attendee(display_name='Al G.', full_name='Al Grogan', email='groganal@gmail.com', reference='MACQ-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Vladimir R.', full_name='Vladimir Rychkov', email='vladimir.rychkov@fijowave.com',
#              reference='MJEP-1', level=3, exhibitor=False),
#     Attendee(display_name='David G.', full_name='David Gibbons', email='dgibbons@eircom.net', reference='MLDZ-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Vincent L.', full_name='Vincent Lonij', email='vlonij@gmail.com', reference='NE5J-1',
#              level=4, exhibitor=False), Attendee(display_name='Harshvardhan P.', full_name='Harshvardhan Pandit',
#                                                  email='harshvardhan.pandit@adaptcentre.ie', reference='NEUP-1',
#                                                  level=3, exhibitor=False),
#     Attendee(display_name='Allen T.', full_name='Allen Thomas Varghese', email='allentv4u@gmail.com',
#              reference='O3RN-1', level=2, exhibitor=False),
#     Attendee(display_name='Carolina D.', full_name='Carolina De Pasquale', email='depasquale.carolina@gmail.com',
#              reference='OIB5-1', level=1, exhibitor=False),
#     Attendee(display_name='Vladyslav S.', full_name='Vladyslav Sitalo', email='root@stvad.org', reference='OSDO-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Mark K.', full_name='Mark Kelly', email='mkellyt@gmail.com', reference='OSM5-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Alihan Z.', full_name='Alihan Zıhna', email='alihanz@gmail.com', reference='OWCM-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Szymon B.', full_name='Szymon Bialkowski', email='xtehninja@gmail.com', reference='P3ZU-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Jamie B.', full_name='Jamie Bouse', email='jbouse@xanadu.ie', reference='PKSS-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='David K.', full_name='David Kernan', email='daveker@google.com', reference='QHVB-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Philip R.', full_name='Philip Roche', email='phil@philroche.net', reference='QPSA-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Barry S.', full_name='Barry Smyth', email='barry.smyth@ucd.ie', reference='QQQC-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Paul S.', full_name='Paul Sexton', email='psexton@sceg.ie', reference='QVP1-1', level=1,
#              exhibitor=False),
#     Attendee(display_name='Owen C.', full_name='Owen corrigan', email='owen.corrigan@gmail.com', reference='QXWQ-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Michael G.', full_name='Michael Grogan', email='michael@michaeljgrogan.com',
#              reference='R4FG-1', level=3, exhibitor=False),
#     Attendee(display_name='Eoin B.', full_name='Eoin Brazil', email='eoin.brazil@gmail.com', reference='RM8B-1',
#              level=4, exhibitor=False),
#     Attendee(display_name='Thomas S.', full_name='Thomas Shaw', email='tshaw@riotgames.com', reference='RR2J-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Conall M.', full_name='Conall Molloy', email='conallmolloy@hotmail.com', reference='RR47-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Richard E.', full_name='Richard Earls', email='richard.earls@bsb.ie', reference='RSDX-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Hans W.', full_name='Hans Wai Chan', email='Hanswai93@gmail.com', reference='SOHM-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Keith M.', full_name='Keith Maxwell', email='keith.maxwell@gmail.com', reference='TFDB-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Vladyslav L.', full_name='Vladyslav Laktionov', email='vladlaktionov87@gmail.com',
#              reference='TMND-1', level=2, exhibitor=False),
#     Attendee(display_name='Simon M.', full_name='Simon Melouah', email='simonmelouah@gmail.com', reference='TWCQ-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Miroslaw B.', full_name='Miroslaw Baran', email='miroslaw@makabra.org', reference='TWRI-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Colette K.', full_name='Colette Kirwan', email='Colette.kirwan23@mail.dcu.ie',
#              reference='UKCC-1', level=1, exhibitor=False),
#     Attendee(display_name='Ben K.', full_name='Ben Klaasen', email='ben@fluidlogic.org', reference='UQQN-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Daniel M.', full_name='Daniel Murphy', email='mail@danielmurphy.ie', reference='UTHY-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Gordon E.', full_name='Gordon Elliott', email='g.elliott@fincad.com', reference='UXY6-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Cosmin P.', full_name='Cosmin Petrache', email='Cosmin.Petrache@sig.com', reference='VDMT-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Angel T.', full_name='Angel Ting', email='angelnting@gmail.com', reference='VHQF-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Severine L.', full_name='Severine Lacaze', email='severine.lacaze@bloombergpolarlake.com',
#              reference='VVRV-1', level=0, exhibitor=False),
#     Attendee(display_name='Maria F.', full_name='Maria Francesca', email='maria@mariafrancesca.net', reference='VZ1I-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Sigmund V.', full_name='Sigmund Vestergaard', email='sigmundv@gmail.com', reference='WEG5-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Daniel B.', full_name='DANIEL BALPARDA', email='BALPARDA@GMAIL.COM', reference='WJX9-1',
#              level=4, exhibitor=False),
#     Attendee(display_name='Eric M.', full_name='Eric Mehes', email='eric.mehes@gmail.com', reference='WNMM-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Daragh C.', full_name='Daragh Casey', email='daragh.casey@gmail.com', reference='WQ1O-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Art K.', full_name='Art K', email='artk.dev@gmail.com', reference='WVN0-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Felipe P.', full_name='Felipe Pina de Sousa', email='felipe@riffstation.com',
#              reference='WYQB-1', level=0, exhibitor=False),
#     Attendee(display_name='Manuel F.', full_name='Manuel Franco', email='manuel@riffstation.com', reference='WYQB-2',
#              level=3, exhibitor=False),
#     Attendee(display_name='Kelan O.', full_name="Kelan O'Connell", email='koconnell@blackrockcollege.com',
#              reference='WZXI-1', level=2, exhibitor=False),
#     Attendee(display_name='John M.', full_name='John Montgomery', email='jmontgomery@blackrockcollege.com',
#              reference='WZXI-2', level=0, exhibitor=False),
#     Attendee(display_name='Salvador M.', full_name='Salvador Marti Román', email='salvador19marti@gmail.com',
#              reference='XBFB-1', level=2, exhibitor=False),
#     Attendee(display_name='Paul D.', full_name='Paul Delany', email='pauldelany@gmail.com', reference='XE1Z-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Lal S.', full_name='Lal Singh Dhaila', email='dhailal@tcd.ie', reference='XIZB-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Ayush G.', full_name='Ayush Ghai', email='ghaia@tcd.ie', reference='XIZB-2', level=1,
#              exhibitor=False),
#     Attendee(display_name='Beth C.', full_name='Beth Craig', email='bethcraig100178@gmail.com', reference='XZUW-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Peter M.', full_name='Peter Mulholland', email='peter.mulholland@yahoo.co.uk',
#              reference='Y1XM-1', level=3, exhibitor=False),
#     Attendee(display_name='Leonardo G.', full_name='Leonardo Giordani', email='giordani.leonardo@gmail.com',
#              reference='Y8J0-1', level=3, exhibitor=False),
#     Attendee(display_name='Peter O.', full_name='Peter Ogden', email='ogden@xilinx.com', reference='YDYG-1', level=3,
#              exhibitor=False),
#     Attendee(display_name='Erol S.', full_name='Erol Selitektay', email='selitektay@gmail.com', reference='YO57-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Chiara C.', full_name='Chiara Cotroneo', email='chiara.cotroneo@ucdconnect.ie',
#              reference='YYCV-1', level=3, exhibitor=False),
#     Attendee(display_name='Ivan K.', full_name='Ivan Kavaliou', email='ikavalio@pm.me', reference='Z1W8-1', level=2,
#              exhibitor=False),
#     Attendee(display_name='Rondineli G.', full_name='Rondineli Gomes de Araujo', email='rondineli@riffstation.com',
#              reference='Z2MS-1', level=2, exhibitor=False),
#     Attendee(display_name='Vitor C.', full_name='Vitor Cali', email='vitor@riffstation.com', reference='Z2MS-2',
#              level=2, exhibitor=False),
#     Attendee(display_name='Enrico A.', full_name='Enrico Alemani', email='enrico.alemani@gmail.com', reference='Z4RG-1',
#              level=2, exhibitor=False),
#     Attendee(display_name='Bianca P.', full_name='Bianca Prodan', email='b.prodan95@gmail.com', reference='Z7IG-1',
#              level=3, exhibitor=False),
#     Attendee(display_name='Guillem A.', full_name='Guillem Abello', email='guillem.abello@edgetier.com',
#              reference='ZBXD-1', level=3, exhibitor=False),
#     Attendee(display_name='Miguel G.', full_name='Miguel Grinberg', email='miguel.grinberg@edgetier.com',
#              reference='ZBXD-2', level=3, exhibitor=False),
#     Attendee(display_name='Brenda P.', full_name='Brenda Pessoa', email='bnviana@gmail.com', reference='ZLDL-1',
#              level=1, exhibitor=False),
#     Attendee(display_name='Vladimir B.', full_name='Vladimir Berkutov', email='vladimirb@indeed.com',
#              reference='ZMDP-1', level=4, exhibitor=False)]

create_badges(data)
