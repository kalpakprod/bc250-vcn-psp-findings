"""Execute the actual PIO override tail with sampled CS/CLK levels.

Starts after header match and first payload pull. Not a PIO timing, header,
DMA/autopull, synchronizer or electrical simulator. In particular it cannot
establish first-bit timing or HOLD-to-high-Z safety. It exposes missing aborts.
"""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "waveshare-adapter-safe-v001/src/rig/spi_toctou.pio"

class OverrideTrace:
    """Instruction-level override-tail trace, with no synthetic timeout recovery."""

    def __init__(self, payload: bytes):
        if not payload:
            raise ValueError("empty payload")
        lines = SOURCE.read_text().splitlines()
        self.code = []
        self.labels = {}
        started = False
        for line in lines:
            line = line.split(";", 1)[0].strip()
            if line == "nop                   side 0":
                started = True
            if not started or not line or line.startswith("."):
                continue
            if line.endswith(":"):
                self.labels[line[:-1]] = len(self.code)
            else:
                instruction, side = line.rsplit("side", 1)
                self.code.append((instruction.strip(), int(side)))
        if not self.code:
            raise ValueError("override tail not found")
        self.bits = [byte >> shift & 1 for byte in payload for shift in range(7, -1, -1)]
        self.y = len(self.bits) - 1
        self.pc = 0
        self.cs = self.clk = 0
        self.hold = 1
        self.driving = False
        self.sent = []
        self.outputs = []
        self.finished = False

    def levels(self, *, cs: int, clk: int) -> None:
        """Advance actual instructions until a wait stalls or one-shot finishes."""
        self.cs, self.clk = cs, clk
        for _ in range(64):
            if self.finished:
                return
            op, side = self.code[self.pc]
            self.hold = side
            self.outputs.append((self.driving, self.hold))
            words = op.replace(",", "").split()
            if words[0] == "wait":
                value, pin = int(words[1]), int(words[3])
                if (self.cs if pin == 1 else self.clk) != value:
                    return
            elif words[:2] == ["set", "pindirs"]:
                self.driving = bool(int(words[2]))
                self.outputs.append((self.driving, self.hold))
            elif words[:2] == ["out", "pins"]:
                if len(self.sent) == len(self.bits):
                    return  # no payload left: FIFO stall, not successful completion
                self.sent.append(self.bits[len(self.sent)])
            elif words[0] == "jmp":
                if words[1] == "finished":
                    self.finished = True
                    return
                if words[1] != "y--":
                    raise ValueError(f"unsupported branch: {op}")
                previous = self.y
                self.y = (self.y - 1) & 0xFFFFFFFF
                if previous:
                    self.pc = self.labels[words[2]]
                    continue
            elif words[0] != "nop":
                raise ValueError(f"unsupported override instruction: {op}")
            self.pc += 1
        raise RuntimeError("override instruction budget exhausted")
