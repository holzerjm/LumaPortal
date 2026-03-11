import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import BADGE_WIDTH, BADGE_HEIGHT, EVENT_NAME, FONTS_DIR, STATIC_DIR
from src.models import Guest

LOGO_PATH = STATIC_DIR / "images" / "toa-black.png"

logger = logging.getLogger(__name__)


def _get_font(bold: bool = False, size: int = 36) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to default if custom fonts aren't available."""
    names = (
        ["Inter-Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["Inter-Regular.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        path = FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        return ImageFont.load_default(size=size)


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    bold: bool,
    start_size: int,
    min_size: int = 24,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find the largest font size that fits within max_width."""
    size = start_size
    while size >= min_size:
        font = _get_font(bold=bold, size=size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font, [text]
        size -= 2

    font = _get_font(bold=bold, size=min_size)
    words = text.split()
    if len(words) >= 2:
        mid = len(words) // 2
        return font, [" ".join(words[:mid]), " ".join(words[mid:])]
    return font, [text]


def generate_badge(
    name: str,
    company: str = "",
    job_title: str = "",
    event_name: str = "",
) -> Image.Image:
    """Generate a landscape badge (100mm × 62mm) for the Brother QL continuous roll."""
    width, height = BADGE_WIDTH, BADGE_HEIGHT
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    margin = 40
    usable_width = width - margin * 2
    event = event_name or EVENT_NAME
    cx = width // 2  # center x

    # ── Centered logo ──
    logo_bottom = 30
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((480, 240), Image.LANCZOS)
            logo_x = cx - logo.width // 2
            logo_y = 25
            img.paste(logo, (logo_x, logo_y), logo)
            logo_bottom = logo_y + logo.height + 8
        except Exception as e:
            logger.warning(f"Could not load logo for badge: {e}")

    # "Innovate Together" centered under logo
    tagline_font = _get_font(bold=True, size=32)
    draw.text((cx, logo_bottom), "Innovate Together", font=tagline_font, fill="#C79100", anchor="mt")

    # Event name under tagline
    event_font = _get_font(bold=False, size=26)
    draw.text((cx, logo_bottom + 40), event, font=event_font, fill="#888888", anchor="mt")

    # Separator
    sep_y = logo_bottom + 80
    draw.line([(margin, sep_y), (width - margin, sep_y)], fill="#cccccc", width=2)

    # ── Name — big and centered ──
    content_top = sep_y + 15
    content_bottom = height - 45
    content_mid_y = (content_top + content_bottom) // 2

    name_font, name_lines = _fit_text(
        draw, name, usable_width, bold=True, start_size=180, min_size=60
    )
    line_h = name_font.size + 12
    total_name_h = len(name_lines) * line_h

    # Detail heights
    detail_h = 0
    if company:
        detail_h += 50
    if job_title:
        detail_h += 42
    gap = 18 if detail_h else 0
    total_block = total_name_h + gap + detail_h
    block_top = content_mid_y - total_block // 2

    for i, line in enumerate(name_lines):
        draw.text(
            (cx, block_top + i * line_h),
            line,
            font=name_font,
            fill="black",
            anchor="mt",
        )

    # Company
    detail_y = block_top + total_name_h + gap
    if company:
        company_font, company_lines = _fit_text(
            draw, company, usable_width, bold=False, start_size=42, min_size=24
        )
        for i, line in enumerate(company_lines):
            draw.text(
                (cx, detail_y + i * (company_font.size + 6)),
                line,
                font=company_font,
                fill="#444444",
                anchor="mt",
            )
        detail_y += len(company_lines) * (company_font.size + 6) + 6

    # Job title
    if job_title:
        title_font = _get_font(bold=False, size=34)
        draw.text((cx, detail_y), job_title, font=title_font, fill="#666666", anchor="mt")

    # Bottom border
    draw.line([(margin, height - 25), (width - margin, height - 25)], fill="#cccccc", width=2)

    return img


def generate_badge_for_guest(guest: Guest) -> Image.Image:
    """Generate a badge from a Guest object."""
    return generate_badge(
        name=guest.name,
        company=guest.company,
        job_title=guest.job_title,
    )
