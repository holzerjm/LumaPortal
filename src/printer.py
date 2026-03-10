import asyncio
import logging
from PIL import Image

from src.config import PRINTER_MODEL, LABEL_SIZE, PRINTER_URI
from src import database as db

logger = logging.getLogger(__name__)

# Track printer availability
_printer_available: bool | None = None


def check_printer_status() -> dict:
    """Check if a Brother QL printer is connected."""
    global _printer_available
    try:
        from brother_ql.backends.helpers import discover
        available = discover(backend_identifier="pyusb")
        if available:
            _printer_available = True
            return {
                "connected": True,
                "printers": [
                    {"identifier": p["identifier"], "model": PRINTER_MODEL}
                    for p in available
                ],
            }
        _printer_available = False
        return {"connected": False, "message": "No Brother QL printer found via USB"}
    except Exception as e:
        _printer_available = False
        return {"connected": False, "message": str(e)}


def _get_printer_uri() -> str:
    """Get the printer URI, using config or auto-discovery."""
    if PRINTER_URI:
        return PRINTER_URI
    try:
        from brother_ql.backends.helpers import discover
        available = discover(backend_identifier="pyusb")
        if available:
            return available[0]["identifier"]
    except Exception:
        pass
    raise RuntimeError("No printer URI configured and auto-discovery failed")


def print_badge(image: Image.Image) -> bool:
    """Send a badge image to the Brother QL printer. Returns True on success."""
    try:
        from brother_ql.raster import BrotherQLRaster
        from brother_ql.conversion import convert
        from brother_ql.backends.helpers import send

        uri = _get_printer_uri()
        qlr = BrotherQLRaster(PRINTER_MODEL)

        instructions = convert(
            qlr=qlr,
            images=[image],
            label=LABEL_SIZE,
            rotate="auto",
            threshold=70,
            dither=False,
            compress=False,
            red=False,
            dpi_600=False,
            hq=True,
            cut=True,
        )

        send(
            instructions=instructions,
            printer_identifier=uri,
            backend_identifier="pyusb",
            blocking=True,
        )
        logger.info(f"Badge printed successfully on {uri}")
        return True

    except Exception as e:
        logger.error(f"Print failed: {e}")
        raise


async def print_badge_async(image: Image.Image, guest_api_id: str):
    """Print a badge in a background thread and mark it in the database."""
    try:
        await asyncio.to_thread(print_badge, image)
        await db.mark_badge_printed(guest_api_id)
        logger.info(f"Badge printed for {guest_api_id}")
    except Exception as e:
        logger.warning(f"Badge print failed for {guest_api_id}: {e}")
        # Save the image as fallback so it can be printed manually
        fallback_path = f"data/badge_{guest_api_id}.png"
        try:
            image.save(fallback_path)
            logger.info(f"Badge image saved to {fallback_path} for manual printing")
        except Exception:
            pass
