"""Prepare RAM-only CDC staging commands from an exact, verified plan window.

No serial I/O, GPIO operation or arm command. The firmware verifies the payload
SHA-256; full-image identities and window membership are checked here on host.
Transaction-index selection is not implemented by the experimental PIO rig.
"""
import hashlib
from image_pack import SparseImage
from toctou_plan import TOCTOUPlan


def window_commands(plan: TOCTOUPlan, images: dict[str, SparseImage],
                    window_index: int) -> list[str]:
    plan.verify_images(images)
    if window_index < 0 or window_index >= len(plan.windows):
        raise ValueError("unknown plan window")
    window = plan.windows[window_index]
    size = window.end - window.start
    if size > 4096 or window.end > 0x1000000:
        raise ValueError("window exceeds responder staging capacity")
    data = images[window.image].read(window.start, size)
    digest = hashlib.sha256(data).hexdigest()
    commands = ["MODE FLASH", f"RIG_BEGIN {window.start:X} {size} {digest}"]
    for offset in range(0, size, 96):
        commands.append(f"RIG_LOAD {offset:X} {data[offset:offset+96].hex()}")
    commands += ["RIG_COMMIT", f"RIG_PREPARE {window.read_index}", "RIG_STATUS"]
    return commands
