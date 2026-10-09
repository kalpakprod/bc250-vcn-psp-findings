"""Optimistic first-bit lower bound from the actual rig PIO instruction path.

Assumes final header CLK falling is observed instantly, exact header match,
first payload already in TX FIFO, and zero GPIO/HOLD delays. Real timing can
only be worse. This is NOT a measurement of BC250 SPI or RP2350 pad timing.
"""
from fractions import Fraction
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "waveshare-adapter-safe-v001/src/rig/spi_toctou.pio"


def first_output_path(source: str) -> tuple[str, ...]:
    """Trace last header falling wait through matched branch to first output."""
    instructions = []
    labels = {}
    for raw in source.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line or line.startswith("."):
            continue
        if line.endswith(":"):
            labels[line[:-1]] = len(instructions)
        else:
            instructions.append(" ".join(line.split()))
    # Last capture iteration: wait 0 follows one rising wait and MOSI sample.
    pc = labels["capture"] + 2
    if instructions[pc] != "wait 0 pin 2 side 1":
        raise ValueError("unsupported final header falling-edge instruction")
    path = []
    for _ in range(len(instructions)):
        op = instructions[pc]
        path.append(op)
        if op.startswith("out pins, 1 "):
            return tuple(path)
        # y-- falls through at end of header, x!=y falls through for exact match.
        if op.startswith("jmp ") and not (
            op.startswith("jmp y-- capture ") or op.startswith("jmp x!=y no_match ")
        ):
            raise ValueError(f"unsupported timing branch: {op}")
        if "[" in op:
            raise ValueError("instruction delays require a new timing analysis")
        pc += 1
        if pc >= len(instructions):
            break
    raise ValueError("first payload output is not reachable on matched path")


def first_bit_margin(pio_hz: int, spi_hz: int) -> Fraction:
    """Optimistic setup margin in PIO cycles; <=0 cannot establish first bit."""
    if pio_hz <= 0 or spi_hz <= 0:
        raise ValueError("frequencies must be positive")
    cycles = len(first_output_path(SOURCE.read_text())) - 1
    return Fraction(pio_hz, 2 * spi_hz) - cycles
