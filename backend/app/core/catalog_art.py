"""Artwork for the academy's language and computing course families."""

from html import escape
from uuid import NAMESPACE_URL, uuid5

_LANGUAGE_COURSES = {
    uuid5(NAMESPACE_URL, f"scholward-academy/language-starters/{source}/{target}"): target
    for source in ("uz", "en", "ru", "ko")
    for target in ("uz", "en", "ru", "ko")
    if source != target
}

# Each subject has its own palette, recognizable lettering and illustration.
_ART = {
    "uz": (
        "#103c38",
        "#216054",
        "#f4c18c",
        "O‘ZBEK TILI",
        "Salom!",
        "O‘",
        '<path d="M892 28 1118 253 892 478 666 253Z M892 69 1077 253 892 437 707 253Z" fill="none" stroke="#ffdaaa" stroke-opacity=".55" stroke-width="2"/><path d="m892 95 159 158-159 158-159-158Z" fill="#1c4a42"/><path d="m665 204 45 49-45 49-45-49Z M1119 204l45 49-45 49-45-49Z" fill="#f4c18c" fill-opacity=".65"/>',
    ),
    "en": (
        "#222f50",
        "#434b7d",
        "#ddd9ff",
        "ENGLISH",
        "Hello!",
        "Aa",
        '<circle cx="978" cy="218" r="202" fill="#8f8bd5" fill-opacity=".34"/><path d="M667 133h393a53 53 0 0 1 53 53v131a53 53 0 0 1-53 53h-258l-80 61v-61h-55a53 53 0 0 1-53-53V186a53 53 0 0 1 53-53Z" transform="rotate(-8 860 244)" fill="#272f54" stroke="#e1dfff" stroke-width="2" stroke-opacity=".65"/><path d="M1085 78h46m-23-23v46" stroke="#ede6ff" stroke-linecap="round" stroke-width="5"/>',
    ),
    "ru": (
        "#472641",
        "#793e60",
        "#fbd1c4",
        "РУССКИЙ ЯЗЫК",
        "Привет!",
        "Я",
        '<circle cx="888" cy="233" r="169" fill="#f9b4a4" fill-opacity=".64"/><circle cx="888" cy="233" r="193" fill="none" stroke="#f6cbbc" stroke-opacity=".73" stroke-width="2"/><path d="M678 357 1074 64m-364 335 397-294" fill="none" stroke="#f6cbbc" stroke-opacity=".39" stroke-width="2"/><circle cx="1084" cy="101" r="15" fill="#ffd8c6"/><circle cx="718" cy="404" r="10" fill="#ffd8c6"/>',
    ),
    "ko": (
        "#48271e",
        "#834b35",
        "#ffdbad",
        "한국어",
        "안녕하세요!",
        "한",
        '<rect x="712" y="78" width="355" height="340" rx="66" transform="rotate(12 891 248)" fill="#e49462" fill-opacity=".73"/><rect x="728" y="76" width="328" height="330" rx="60" transform="rotate(-10 891 244)" fill="#3c251d" stroke="#ffdbad" stroke-opacity=".78" stroke-width="2"/><path d="M745 311h294m-294-82h294m-294-82h294m-217-55v306m137-306v306" stroke="#ffdbad" stroke-width="1.5" stroke-opacity=".19"/>',
    ),
    "html": (
        "#232831",
        "#3b465c",
        "#ffbb8f",
        "HTML / CSS",
        "Web development",
        "</>",
        '<rect x="665" y="99" width="468" height="304" rx="31" fill="#171d28" stroke="#a2abc5" stroke-width="2"/><path d="M665 155h468" stroke="#a2abc5" stroke-opacity=".55" stroke-width="2"/><circle cx="702" cy="127" r="6" fill="#ffa88c"/><circle cx="725" cy="127" r="6" fill="#f4d9a8"/><circle cx="748" cy="127" r="6" fill="#a6d5c9"/><path d="M712 345h118m25 0h79m21 0h126" stroke="#a2abc5" stroke-opacity=".42" stroke-width="5" stroke-linecap="round"/>',
    ),
    "python": (
        "#233b29",
        "#426345",
        "#e9db8d",
        "PYTHON",
        "Programming",
        "Py",
        '<path d="M886 79h147l83 145-83 145H886l-83-145Z" fill="#799761" fill-opacity=".58"/><path d="M781 150h149l75 130-75 130H781l-75-130Z" fill="#1f3927" stroke="#e9db8d" stroke-opacity=".63" stroke-width="2"/><path d="M1009 117h75m-38-38v76M698 105h58m-29-29v58" stroke="#e9db8d" stroke-opacity=".62" stroke-width="3" stroke-linecap="round"/>',
    ),
}

_COMPUTING_LABELS = {
    "html": {
        "uz": "Veb dasturlash",
        "en": "Web development",
        "ru": "Веб-разработка",
        "ko": "웹 개발",
    },
    "python": {
        "uz": "Dasturlash",
        "en": "Programming",
        "ru": "Программирование",
        "ko": "프로그래밍",
    },
}


def render_subject_banner(course) -> bytes | None:
    subject = _LANGUAGE_COURSES.get(course.id)
    if subject is None:
        title = course.title.casefold()
        if "html" in title or "css" in title:
            subject = "html"
        elif "python" in title or "파이썬" in title:
            subject = "python"
    if subject not in _ART:
        return None

    dark, light, accent, label, example, glyph, illustration = _ART[subject]
    if subject in _COMPUTING_LABELS:
        example = _COMPUTING_LABELS[subject].get(course.language, example)
    type_color = "#4b2741" if subject == "ru" else accent
    hero_size = 70 if subject in _COMPUTING_LABELS else 95
    glyph_size = 138 if subject == "html" else 185
    label_y, example_y = (149, 279) if subject in _COMPUTING_LABELS else (157, 292)
    glyph_x = 860 if subject == "python" else 892
    font = "Noto Sans KR, Apple SD Gothic Neo, Arial, sans-serif"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 480" role="img" aria-label="{escape(course.title)}">
<defs>
  <linearGradient id="tone" x1="0" x2="1" y1="0" y2="1"><stop stop-color="{dark}"/><stop offset="1" stop-color="{light}"/></linearGradient>
  <pattern id="grain" width="46" height="46" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#fff" fill-opacity=".22"/></pattern>
</defs>
<rect width="1200" height="480" fill="url(#tone)"/><rect width="1200" height="480" fill="url(#grain)"/>
<path d="M65 83h70m-70 285h530" stroke="{accent}" stroke-opacity=".68" stroke-width="2"/>
{illustration}
<text x="{glyph_x}" y="303" text-anchor="middle" fill="{type_color}" font-family="{font}" font-size="{glyph_size}" font-weight="800">{escape(glyph)}</text>
<text x="62" y="{label_y}" fill="{accent}" font-family="{font}" font-size="28" font-weight="700" letter-spacing="5">{escape(label)}</text>
<text x="59" y="{example_y}" fill="#fff7ec" font-family="{font}" font-size="{hero_size}" font-weight="800" letter-spacing="-1">{escape(example)}</text>
</svg>'''.encode()
