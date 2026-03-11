import asyncio
import logging
from PIL import Image

from src.config import PRINTER_MODEL, LABEL_SIZE, PRINTER_URI
from src import database as db

logger = logging.getLogger(__name__)

# Fix brother_ql compatibility with Pillow 10+
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# Brother QL USB vendor/product IDs
_BROTHER_VENDOR = 0x04F9
_QL820NWB_PRODUCT = 0x209D

# Track printer availability
_printer_available: bool | None = None


def _find_usb_device():
    """Find Brother QL printer via USB."""
    import usb.core

    return usb.core.find(idVendor=_BROTHER_VENDOR, idProduct=_QL820NWB_PRODUCT)


def check_printer_status() -> dict:
    """Check if a Brother QL printer is connected via USB."""
    global _printer_available

    try:
        dev = _find_usb_device()
        if dev:
            _printer_available = True
            return {
                "connected": True,
                "printers": [
                    {
                        "identifier": f"usb://0x{_BROTHER_VENDOR:04x}:0x{_QL820NWB_PRODUCT:04x}",
                        "model": PRINTER_MODEL,
                    }
                ],
            }
    except Exception:
        pass

    _printer_available = False
    return {"connected": False, "message": "No Brother QL printer found via USB"}


def _get_printer_uri() -> str:
    """Get a clean printer URI for brother_ql."""
    if PRINTER_URI:
        return PRINTER_URI
    return f"usb://0x{_BROTHER_VENDOR:04x}:0x{_QL820NWB_PRODUCT:04x}"


def print_badge(image: Image.Image) -> bool:
    """Send a badge image to the Brother QL printer via direct USB."""
    import usb.core
    import usb.util
    from brother_ql.raster import BrotherQLRaster
    from brother_ql.conversion import convert

    # Generate raster instructions with two-color mode
    # The QL-820NWB requires red=True (two-color raster format) even for
    # black-only printing on DK-2205 rolls.
    qlr = BrotherQLRaster(PRINTER_MODEL)
    instructions = convert(
        qlr=qlr,
        images=[image],
        label=LABEL_SIZE,
        rotate="auto",
        threshold=70,
        dither=False,
        compress=False,
        red=True,
        dpi_600=False,
        hq=True,
        cut=True,
    )

    # Send raw via pyusb (bypasses brother_ql's send() which has
    # unreliable status parsing for the QL-820NWB)
    dev = _find_usb_device()
    if not dev:
        raise RuntimeError("Brother QL printer not found on USB")

    try:
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]
        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )
        ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_IN,
        )

        # Drain any stale status messages
        for _ in range(10):
            try:
                ep_in.read(32, timeout=100)
            except usb.core.USBTimeoutError:
                break
            except Exception:
                break

        # Send instructions in chunks
        chunk_size = 4096
        for i in range(0, len(instructions), chunk_size):
            ep_out.write(instructions[i : i + chunk_size], timeout=15000)

        # Wait for print completion status
        import time

        time.sleep(3)
        for _ in range(5):
            try:
                data = bytes(ep_in.read(32, timeout=3000))
                if len(data) >= 20:
                    status_type = data[18]
                    if status_type == 1:  # Printing completed
                        logger.info("Badge printed via brother_ql (two-color mode)")
                        return True
                    elif status_type == 2:  # Error
                        err1, err2 = data[8], data[9]
                        raise RuntimeError(
                            f"Printer error: err1={err1:08b}, err2={err2:08b}"
                        )
                    elif status_type == 6:  # Phase change
                        continue  # Wait for completion
            except usb.core.USBTimeoutError:
                break
            except RuntimeError:
                raise
            except Exception:
                break

        # If we get here, we sent data but didn't get explicit confirmation.
        # The QL-820NWB often prints successfully without sending the
        # "printing completed" status byte. Log as success.
        logger.info("Badge sent to printer (no explicit completion status)")
        return True

    finally:
        # Release the USB interface so subsequent prints can claim it
        usb.util.dispose_resources(dev)


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
