"""Host-side estimate for an SPI mode-0 first-bit deadline."""

from fractions import Fraction


def mode0_first_bit_margin_cycles(
    pio_hz: int,
    spi_hz: int,
    *,
    assumed_edge_to_wait_cycles: int = 4,
) -> Fraction:
    """Estimate cycles remaining before the first mode-0 sample edge.

    The estimate starts at the final command/address falling edge. It assumes
    half an SPI bit period remains, subtracts an explicitly assumed delay from
    that edge until the PIO WAIT detects it, then subtracts three PIO
    instruction cycles (`jmp x--`, `set x`, `out pins`) before the first output
    bit is updated in `spi_inject.pio`.

    The assumed four-cycle allowance includes synchronizer, phase, and WAIT
    detection delay. This arithmetic excludes pad delay, setup time, and clock
    jitter, and cannot establish hardware timing.
    """
    if pio_hz <= 0 or spi_hz <= 0:
        raise ValueError("clock frequencies must be positive")
    if assumed_edge_to_wait_cycles < 0:
        raise ValueError("assumed edge-to-WAIT delay must be non-negative")

    available_cycles = Fraction(pio_hz, 2 * spi_hz)
    required_cycles = assumed_edge_to_wait_cycles + 3
    return available_cycles - required_cycles
