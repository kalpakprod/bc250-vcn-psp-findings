"""Host-only model of the legacy PIO selector/filter ordering."""

from __future__ import annotations

from dataclasses import dataclass

READ_DATA = 0x03


@dataclass(frozen=True)
class SelectorFilter:
    """Address and selector state written after a matching read header."""

    address: int
    inject: bool


@dataclass(frozen=True)
class ReadTransaction:
    """SPI opcode and transaction-start address."""

    opcode: int
    address: int


@dataclass(frozen=True)
class SelectorStep:
    """Selector state sampled at CS-low and after trigger processing."""

    selector_at_cs: bool
    path: str
    matched_filter: SelectorFilter | None
    selector_after_header: bool


def trace_selector_queue(
    filters: tuple[SelectorFilter, ...],
    transactions: tuple[ReadTransaction, ...],
    initial_selector: bool = False,
) -> tuple[SelectorStep, ...]:
    """Trace legacy PIO control flow, not SPI timing or electrical behavior."""
    selector = initial_selector
    filter_index = 0
    steps = []

    for transaction in transactions:
        selector_at_cs = selector
        matched_filter = None
        if (
            transaction.opcode == READ_DATA
            and filter_index < len(filters)
            and transaction.address == filters[filter_index].address
        ):
            matched_filter = filters[filter_index]
            selector = matched_filter.inject
            filter_index += 1

        steps.append(
            SelectorStep(
                selector_at_cs=selector_at_cs,
                path="inject" if selector_at_cs else "pass-through",
                matched_filter=matched_filter,
                selector_after_header=selector,
            )
        )

    return tuple(steps)
