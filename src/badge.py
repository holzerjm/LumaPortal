import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import BADGE_WIDTH, BADGE_HEIGHT, EVENT_NAME, FONTS_DIR
from src.models import Guest

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
    # Fallback to Pillow's default
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        return ImageFont.load_default(size=size)


def _auto_size_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    bold: bool,
    start_size: int,
    min_size: int = 18,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find the largest font size that fits text within max_width. Returns font and wrapped lines."""
    size = start_size
    while size >= min_size:
        font = _get_font(bold=bold, size=size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            return font, [text]
        size -= 2

    # At min size, try wrapping to two lines
    font = _get_font(bold=bold, size=min_size)
    words = text.split()
    if len(words) >= 2:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        return font, [line1, line2]

    return font, [text]


def generate_badge(
    name: str,
    company: str = "",
    job_title: str = "",
    event_name: str = "",
) -> Image.Image:
    """Generate a badge image for thermal printing."""
    width, height = BADGE_WIDTH, BADGE_HEIGHT
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    margin = 50
    usable_width = width - margin * 2
    event = event_name or EVENT_NAME

    # Event name at top
    event_font = _get_font(bold=False, size=28)
    draw.text(
        (width // 2, 80),
        event,
        font=event_font,
        fill="#888888",
        anchor="mt",
    )

    # Thin separator line
    draw.line([(margin, 130), (width - margin, 130)], fill="#cccccc", width=2)

    # Name (the hero element) — centered vertically
    name_y = height // 2 - 80
    name_font, name_lines = _auto_size_text(
        draw, name, usable_width, bold=True, start_size=72, min_size=32
    )
    line_height = name_font.size + 8
    for i, line in enumerate(name_lines):
        draw.text(
            (width // 2, name_y + i * line_height),
            line,
            font=name_font,
            fill="black",
            anchor="mt",
        )

    # Company below name
    detail_y = name_y + len(name_lines) * line_height + 30
    if company:
        company_font, company_lines = _auto_size_text(
            draw, company, usable_width, bold=False, start_size=36, min_size=20
        )
        for i, line in enumerate(company_lines):
            draw.text(
                (width // 2, detail_y + i * (company_font.size + 4)),
                line,
                font=company_font,
                fill="#444444",
                anchor="mt",
            )
        detail_y += len(company_lines) * (company_font.size + 4) + 10

    # Job title
    if job_title:
        title_font = _get_font(bold=False, size=28)
        draw.text(
            (width // 2, detail_y),
            job_title,
            font=title_font,
            fill="#666666",
            anchor="mt",
        )

    # Bottom border line
    draw.line(
        [(margin, height - 60), (width - margin, height - 60)],
        fill="#cccccc",
        width=2,
    )

    return img


def generate_badge_for_guest(guest: Guest) -> Image.Image:
    """Generate a badge from a Guest object."""
    return generate_badge(
        name=guest.name,
        company=guest.company,
        job_title=guest.job_title,
    )
