"""TC-UX-01 (RRS-NF-005), automated part: labels, landmarks, defaults and status colours.

The walkthrough with a real first-time user is manual: docs/TC-UX-01_usability_walkthrough.md
"""
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = sorted((ROOT / "templates").glob("*.html"))
A11Y = (ROOT / "static" / "a11y.css").read_text(encoding="utf-8")
STYLE = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels, self.fields, self.images, self.tags = set(), [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "label" and a.get("for"):
            self.labels.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit", "button"):
            self.fields.append(a)
        if tag == "img":
            self.images.append(a)


def _scan(path):
    scan = Scan()
    scan.feed(path.read_text(encoding="utf-8"))
    return scan


def test_every_form_field_has_a_label():
    problems = []
    for path in TEMPLATES:
        scan = _scan(path)
        for field in scan.fields:
            named = field.get("aria-label") or field.get("aria-labelledby")
            if not named and field.get("id") not in scan.labels:
                problems.append(f"{path.name}: field {field.get('id') or field.get('name') or '?'} has no label")
    assert not problems, problems


def test_images_have_alt_text():
    for path in TEMPLATES:
        for image in _scan(path).images:
            assert "alt" in image, f"{path.name}: image without alt"


def test_base_page_has_language_main_landmark_and_skip_link():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    assert re.search(r'<html[^>]*\blang="en"', base)
    assert 'class="skip-link"' in base and 'href="#main"' in base
    assert re.search(r'<main[^>]*\bid="main"', base)
    assert "a11y.css" in base


def test_messages_are_announced_to_screen_readers():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    assert 'role="alert"' in base


def test_search_form_has_sensible_defaults():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"\.value\s*=\s*todayLocal\(\)", js)  # travel date starts at today
    assert re.search(r"\.min\s*=\s*todayLocal\(\)", js)  # past dates are not offered


def test_no_configuration_needed_to_start():
    from config import Config

    assert Config.SECRET_KEY and Config.IDLE_TIMEOUT_SECONDS > 0  # every setting has a default


# ---- colour contrast (WCAG AA = 4.5:1 for normal text) ---------------------------------
def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(foreground, background):
    a, b = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def test_contrast_helper_matches_known_values():
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0
    assert contrast("#777777", "#ffffff") < 4.5


def test_status_badge_colours_meet_aa_contrast():
    pairs = re.findall(r"--b-(\w+)-bg:\s*(#[0-9a-fA-F]{6});\s*--b-\1-fg:\s*(#[0-9a-fA-F]{6})", A11Y)
    assert {name for name, _, _ in pairs} == {"confirmed", "rac", "waitlisted", "cancelled", "provisional"}
    for name, background, foreground in pairs:
        assert contrast(foreground, background) >= 4.5, name


def test_every_status_badge_also_has_a_symbol():
    for name in ("confirmed", "rac", "waitlisted", "cancelled", "provisional"):
        assert re.search(rf"\.badge-{name}::before\s*\{{\s*content:", A11Y), name


def test_main_page_colours_meet_aa_contrast():
    css = {k: v for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", STYLE)}
    for fg, bg in [("ink", "wash"), ("rail", "wash"), ("ok-ink", "ok-bg"), ("err-ink", "err-bg"),
                   ("confirmed", "ok-bg")]:
        assert contrast(css[fg], css[bg]) >= 4.5, (fg, bg)
    assert contrast("#ffffff", css["rail-dark"]) >= 4.5  # top bar text
    assert contrast("#ffffff", css["rail"]) >= 4.5  # button text
