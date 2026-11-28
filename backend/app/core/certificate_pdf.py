from functools import lru_cache
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from app.core.schemes.certificate import CertificateVerificationResponse
from app.core.site import SCHOLWARD_PUBLIC_URL

FONT = "CertificateSans"
COPY = {
    "uz": (
        "Kursni tamomlaganlik sertifikati",
        "Ushbu sertifikat taqdim etiladi",
        "Muvaffaqiyatli yakunlangan kurs",
        "Berilgan sana",
        "Imtihon natijasi",
        "Daraja",
        "Sertifikatni tekshirish",
        "Sertifikat kodi",
        "Boshlang‘ich",
        "O‘rta",
        "Yuqori",
    ),
    "en": (
        "Certificate of Completion",
        "This certificate is awarded to",
        "Successfully completed course",
        "Date issued",
        "Exam score",
        "Level",
        "Verify this certificate",
        "Certificate code",
        "Foundation",
        "Intermediate",
        "Advanced",
    ),
    "ru": (
        "Сертификат об окончании курса",
        "Сертификат выдан",
        "Успешно пройденный курс",
        "Дата выдачи",
        "Результат экзамена",
        "Уровень",
        "Проверить сертификат",
        "Код сертификата",
        "Начальный",
        "Средний",
        "Продвинутый",
    ),
    "ko": (
        "과정 수료증",
        "이 수료증을 드립니다",
        "성공적으로 수료한 과정",
        "발급일",
        "시험 점수",
        "등급",
        "수료증 확인",
        "수료증 코드",
        "기초",
        "중급",
        "고급",
    ),
}


@lru_cache
def register_certificate_font() -> None:
    path = Path(__file__).with_name("certificate_assets") / "NotoSansKR-Regular.ttf"
    pdfmetrics.registerFont(TTFont(FONT, str(path)))


def draw_text(pdf: Canvas, value: str, x: float, y: float, size: float, color: str) -> None:
    pdf.setFillColor(HexColor(color))
    pdf.setFont(FONT, size)
    pdf.drawString(x, y, value)


def draw_field(
    pdf: Canvas, value: str, x: float, y: float, size: int, width: float, max_lines: int
) -> None:
    value = " ".join(value.split())
    # Break on words when possible and still fit long unbroken names.
    while True:
        rows = []
        remaining = value
        while remaining:
            end = len(remaining)
            while end > 1 and pdfmetrics.stringWidth(remaining[:end], FONT, size) > width:
                end -= 1
            if end < len(remaining) and " " in remaining[:end]:
                end = remaining[:end].rindex(" ")
            rows.append(remaining[:end])
            remaining = remaining[end:].lstrip()
        if len(rows) <= max_lines:
            break
        size -= 1
    for index, row in enumerate(rows):
        draw_text(pdf, row, x, y - index * (size + 5), size, "#132d29")


def draw_qr(pdf: Canvas, url: str, x: float, y: float) -> None:
    qr = QrCodeWidget(url, barLevel="M")
    x1, y1, x2, y2 = qr.getBounds()
    size = 92
    drawing = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
    drawing.add(qr)
    pdf.setFillColor(HexColor("#ffffff"))
    pdf.roundRect(x, y, size, size, 4, fill=1, stroke=0)
    renderPDF.draw(drawing, pdf, x, y)
    pdf.linkURL(url, (x, y, x + size, y + size))


def render_certificate_pdf(certificate: CertificateVerificationResponse, language: str) -> bytes:
    register_certificate_font()
    language = language if language in COPY else "uz"
    title, awarded, completed, date, score, level, verify, code, *grades = COPY[language]
    grade = grades[{"bronze": 0, "silver": 1, "gold": 2}.get(certificate.achievement_level, 0)]
    query = urlencode({"code": certificate.certificate_code, "lang": language})
    url = f"{SCHOLWARD_PUBLIC_URL}/app/verify.html?{query}"
    output = BytesIO()
    width, height = landscape(A4)
    pdf = Canvas(output, pagesize=(width, height), pageCompression=1)
    pdf.setTitle(f"SCHOLWARD Academy - {title}")
    pdf.setAuthor("SCHOLWARD Academy")

    pdf.setFillColor(HexColor("#fbf8ee"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#143932"))
    pdf.rect(0, 0, 250, height, fill=1, stroke=0)
    pdf.saveState()
    panel = pdf.beginPath()
    panel.rect(0, 0, 250, height)
    pdf.clipPath(panel, stroke=0, fill=0)
    pdf.setStrokeColor(HexColor("#41625a"))
    for radius in (76, 97, 118):
        pdf.circle(180, 439, radius, fill=0, stroke=1)
    pdf.restoreState()
    pdf.setStrokeColor(HexColor("#d4b574"))
    pdf.setLineWidth(1.4)
    crest = pdf.beginPath()
    crest.moveTo(65, 540)
    crest.lineTo(84, 533)
    crest.lineTo(84, 515)
    crest.curveTo(84, 504, 76, 496, 65, 491)
    crest.curveTo(54, 496, 46, 504, 46, 515)
    crest.lineTo(46, 533)
    crest.close()
    pdf.drawPath(crest)
    draw_text(pdf, "S", 58, 508, 22, "#edd6a5")
    draw_text(pdf, "SCHOLWARD", 44, 459, 22, "#ffffff")
    draw_text(pdf, "Academy", 45, 435, 15, "#edd6a5")

    draw_qr(pdf, url, 44, 158)
    pdf.setFillColor(HexColor("#e3c68b"))
    pdf.roundRect(44, 107, 162, 34, 6, fill=1, stroke=0)
    draw_text(pdf, verify, 54, 119, 11, "#143932")
    pdf.linkURL(url, (44, 107, 206, 141))
    draw_text(pdf, code, 44, 78, 9, "#edd6a5")
    draw_text(pdf, certificate.certificate_code, 44, 60, 8, "#ffffff")
    draw_text(pdf, "scholward-academy.vercel.app", 44, 34, 8, "#edd6a5")
    pdf.linkURL(url, (44, 32, 177, 45))

    pdf.setStrokeColor(HexColor("#b28c4d"))
    pdf.setLineWidth(2)
    pdf.line(298, 516, 347, 516)
    draw_field(pdf, title, 298, 465, 31, 493, 2)
    draw_text(pdf, awarded, 298, 374, 13, "#455f57")
    draw_field(pdf, certificate.recipient_name, 298, 327, 37, 490, 3)
    draw_text(pdf, completed, 298, 202, 13, "#455f57")
    draw_field(pdf, certificate.course_title, 298, 169, 22, 490, 3)

    pdf.setStrokeColor(HexColor("#cfc3a8"))
    pdf.setLineWidth(1)
    pdf.line(298, 86, width - 48, 86)
    for x, label, value in (
        (298, date, certificate.issued_at.date().isoformat()),
        (481, score, f"{certificate.score_percent:g}%"),
        (633, level, grade),
    ):
        draw_text(pdf, label, x, 63, 11, "#455f57")
        draw_text(pdf, value, x, 38, 16, "#132d29")
    for inset, weight, color in ((13, 1.25, "#b28c4d"), (19, 0.45, "#d4b574")):
        pdf.setLineWidth(weight)
        pdf.setStrokeColor(HexColor(color))
        pdf.rect(inset, inset, width - 2 * inset, height - 2 * inset, fill=0, stroke=1)
    pdf.showPage()
    pdf.save()
    return output.getvalue()
