#!/usr/bin/env python3
"""BC-250 board voltage sources: which firmware modules can drive a VR register?

Question (bounded, read-only): inside the pinned 5.00-clv firmware corpus, which modules
implement the Super-I/O/EC-window VR mailbox writer - i.e. which modules can stage a
transaction in the EC mailbox (ports 0x2E/0x2F + 0xA20..0xA22 window) and therefore write a
voltage-regulator register - and which modules only touch the shared EC configuration window?

Method: one conjunctive literal-byte detector over the immutable, already-extracted 233-module
corpus. A module is classified VR_MAILBOX_WRITER only when every anchor of the calibrated strong
set is present in its image bytes. Every other module that touches the EC window is recorded as a
bounded negative with its per-anchor hit table. For each writer the EC transport helper bodies and
their call sites (pushed register index + staged value) are enumerated from an objdump disassembly.

Inputs are read-only; nothing in the ROM, the corpus or the NVRAM is written.
Exit 0 = every internal check passed; exit 1 = at least one check failed.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
ROM_SIZE = 16777216
CORPUS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
CENSUS = CORPUS / "census.json"
CENSUS_SHA = "506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39"
PRIOR = ROOT / "evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/fixed-voltage-consumer-result.json"
OUT = pathlib.Path(__file__).resolve().parent / "vr-mailbox-writers-result.json"
DIS_DIR = pathlib.Path(__file__).resolve().parent / "objdump"

# Literal anchors. Every pattern is a byte sequence actually observed in the pinned corpus.
ANCHORS = [
    ("push_cfg_index_2e", "6a2e", "push 0x2e - Super-I/O config index port"),
    ("push_cfg_data_2f", "6a2f", "push 0x2f - Super-I/O config data port"),
    ("mov_al_87", "b087", "mov al,0x87 - config unlock byte"),
    ("imm_ec_window_a20", "200a0000", "little-endian immediate 0x00000a20 - EC data window base"),
    ("push_mbox_65", "6a65", "push 0x65 - mailbox register (command/transaction class)"),
    ("push_mbox_66", "6a66", "push 0x66 - mailbox register (target VR register index)"),
    ("push_mbox_70", "6a70", "push 0x70 - mailbox register (value low byte)"),
    ("push_mbox_63", "6a63", "push 0x63 - mailbox register (transfer count)"),
    ("push_mbox_60", "6a60", "push 0x60 - mailbox register (trigger/commit)"),
    ("test_al_40", "a840", "test al,0x40 - mailbox status-bit poll"),
    # weaker EC-window-only evidence (not part of the strong set)
    ("out_imm_2e", "e62e", "out 0x2e,al - direct config-port write"),
    ("in_imm_2e", "e42e", "in al,0x2e - direct config-port read"),
    ("mov_dx_2e", "ba2e00", "mov dx,0x2e - config index port in dx"),
    ("mov_dx_2f", "ba2f00", "mov dx,0x2f - config data port in dx"),
]
STRONG = [
    "push_cfg_index_2e",
    "push_cfg_data_2f",
    "mov_al_87",
    "imm_ec_window_a20",
    "push_mbox_65",
    "push_mbox_66",
    "push_mbox_70",
    "push_mbox_63",
    "push_mbox_60",
    "test_al_40",
]
EC_WINDOW_ONLY_ANCHORS = ["push_cfg_index_2e", "push_cfg_data_2f", "mov_al_87",
                          "out_imm_2e", "in_imm_2e", "mov_dx_2e", "mov_dx_2f"]
# Calibration: the two VR-controller PEIMs already established as Setup fixed-voltage consumers.
EXPECTED_WRITERS = {"ISL69247-3e1f753a6279", "ISL95712-c0cc17d2d54f"}
PRIOR_VR_STEMS = {"ISL69247-3e1f753a6279", "ISL95712-c0cc17d2d54f"}
# The only other module that reads the Setup variable; must not implement the mailbox writer.
PRIOR_NON_WRITER = "CpuDxe-4fe9d6dc6dfe"

INS_RE = re.compile(r"^\s*([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$")
REG32 = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
REG8 = ("al", "bl", "cl", "dl", "ah", "bh", "ch", "dh")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_all(haystack, needle, limit=64):
    out, start = [], 0
    while len(out) < limit:
        i = haystack.find(needle, start)
        if i < 0:
            break
        out.append(i)
        start = i + 1
    return out


def disassemble(bin_path, stem):
    DIS_DIR.mkdir(exist_ok=True)
    txt = subprocess.run(
        ["objdump", "-D", "-b", "binary", "-m", "i386", "-M", "intel", str(bin_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    (DIS_DIR / (stem + ".objdump.txt")).write_text(txt)
    insns = []
    for line in txt.splitlines():
        m = INS_RE.match(line)
        if not m:
            continue
        rest = m.group(3).strip()
        parts = rest.split(None, 1)
        insns.append({
            "addr": int(m.group(1), 16),
            "raw": m.group(2).strip(),
            "mn": parts[0],
            "ops": parts[1] if len(parts) > 1 else "",
        })
    return insns


def push_arg(insn, regimm):
    """Resolve one `push <operand>` into an immediate when possible."""
    op = insn["ops"].strip()
    if op.startswith("0x"):
        try:
            return int(op, 16), "immediate"
        except ValueError:
            return None, "unparsed"
    reg = op.lower()
    if reg in REG32 or reg in REG8:
        got = regimm.get(reg)
        if got is None:
            return None, "register-unresolved"
        return got[0], "register:%s@0x%x" % (reg, got[1])
    return None, "unresolved"


def analyze_writer(rec, blob, bin_path):
    insns = disassemble(bin_path, rec["stem"])
    a20 = find_all(blob, bytes.fromhex("200a0000"))
    unlock = find_all(blob, bytes.fromhex("b087"))
    call_targets = sorted({int(i["ops"].split()[0], 16) for i in insns
                           if i["mn"] == "call" and i["ops"].startswith("0x")})
    starts = sorted(set(call_targets) | {0})
    helpers = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(blob)
        owned_a20 = [o for o in a20 if start <= o < end]
        owned_unlock = [o for o in unlock if start <= o < end]
        if owned_a20 or owned_unlock:
            helpers.append({
                "entry": "0x%x" % start,
                "owns_ec_window_immediate": ["0x%x" % o for o in owned_a20],
                "owns_unlock_byte": ["0x%x" % o for o in owned_unlock],
                "full_transport_helper": bool(owned_a20 and owned_unlock),
            })
    helper_entries = {int(h["entry"], 16) for h in helpers if h["full_transport_helper"]}
    # linear register-immediate tracking, invalidated by call/ret (bounded heuristic)
    regimm, call_sites = {}, []
    for i, insn in enumerate(insns):
        if insn["mn"] == "mov" and "," in insn["ops"]:
            dst, src = [p.strip() for p in insn["ops"].split(",", 1)]
            if dst.lower() in REG32 + REG8:
                if src.startswith("0x"):
                    try:
                        regimm[dst.lower()] = (int(src, 16), insn["addr"])
                    except ValueError:
                        regimm.pop(dst.lower(), None)
                else:
                    regimm.pop(dst.lower(), None)
        elif insn["mn"] == "xor" and "," in insn["ops"]:
            a, b = [p.strip().lower() for p in insn["ops"].split(",", 1)]
            if a == b and a in REG32 + REG8:
                regimm[a] = (0, insn["addr"])
        elif insn["mn"] in ("call", "ret", "retf"):
            target = None
            if insn["mn"] == "call" and insn["ops"].startswith("0x"):
                target = int(insn["ops"].split()[0], 16)
            if target in helper_entries:
                # Bounded argument recovery: walk back over up to 6 instructions, collect
                # pushes, stop at any control-flow or stack-balancing instruction.
                stoppers = ("call", "ret", "retf", "jmp", "leave", "pop")
                pushes, j = [], i - 1
                while j >= 0 and len(pushes) < 4 and (i - j) <= 6:
                    mn = insns[j]["mn"]
                    if mn == "push":
                        pushes.append(insns[j])
                    elif mn.startswith("j") or mn in stoppers:
                        break
                    elif mn in ("add", "sub") and insns[j]["ops"].startswith(("esp", "sp")):
                        break
                    j -= 1
                pushes.reverse()
                args = []
                for p in pushes:
                    value, how = push_arg(p, regimm)
                    args.append({"raw": p["ops"].strip(), "value": value, "resolution": how,
                                 "at": "0x%x" % p["addr"]})
                site = {"call_addr": "0x%x" % insn["addr"], "helper": "0x%x" % target,
                        "pushes": [a["raw"] for a in args]}
                if len(args) >= 2:
                    site["pushed_register_index"] = args[-1]["value"]
                    site["pushed_register_index_raw"] = args[-1]["raw"]
                    site["staged_value"] = args[-2]["value"]
                    site["staged_value_raw"] = args[-2]["raw"]
                    site["staged_value_resolution"] = args[-2]["resolution"]
                call_sites.append(site)
            regimm = {}
    rom_off = None
    for start in range(rec["ffs_offset"], rec["ffs_offset"] + 0x60):
        if ROM_BYTES[start:start + 2] != b"VZ":
            continue
        if sha256_bytes(ROM_BYTES[start:start + rec["size"]]) == rec["sha256"]:
            rom_off = start
            break
    return {
        "helpers": helpers,
        "call_sites": call_sites,
        "rom_reextraction": {
            "rom_offset": None if rom_off is None else "0x%x" % rom_off,
            "sha256": None if rom_off is None else sha256_bytes(ROM_BYTES[rom_off:rom_off + rec["size"]]),
            "matches_corpus_image": rom_off is not None,
        },
    }


def main():
    checks = 0
    failed = []

    def check(cond, label):
        nonlocal checks
        checks += 1
        if not cond:
            failed.append(label)
        return bool(cond)

    check(ROM.exists(), "donor ROM exists")
    check(ROM.stat().st_size == ROM_SIZE, "donor ROM size == %d" % ROM_SIZE)
    check(sha256_file(ROM) == ROM_SHA, "donor ROM sha256 == pinned")
    global ROM_BYTES
    ROM_BYTES = ROM.read_bytes()
    check(sha256_file(CENSUS) == CENSUS_SHA, "census sha256 == pinned")

    census = json.loads(CENSUS.read_text())
    records = census["records"]
    check(len(records) == 233, "census holds 233 module records")

    images, hash_ok = {}, 0
    for rec in records:
        blob = (CORPUS / (rec["stem"] + ".bin")).read_bytes()
        images[rec["stem"]] = blob
        if sha256_bytes(blob) == rec["sha256"]:
            hash_ok += 1
    check(hash_ok == len(records), "all %d module images match their census sha256" % len(records))

    anchor_offsets, present = {}, {}
    for rec in records:
        blob = images[rec["stem"]]
        offs = {}
        for name, hexpat, _note in ANCHORS:
            o = find_all(blob, bytes.fromhex(hexpat))
            if o:
                offs[name] = ["0x%x" % x for x in o]
        anchor_offsets[rec["stem"]] = offs
        present[rec["stem"]] = set(offs)

    writers, ec_window_only = [], []
    for rec in records:
        stem = rec["stem"]
        if set(STRONG) <= present[stem]:
            entry = {
                "stem": stem, "ui": rec.get("ui") or stem, "type": rec["type"],
                "ffs_guid": rec["ffs_guid"], "ffs_offset": "0x%x" % rec["ffs_offset"],
                "fv_base": "0x%x" % rec["fv_base"], "size": rec["size"],
                "sha256": rec["sha256"], "anchor_offsets": anchor_offsets[stem],
            }
            entry.update(analyze_writer(rec, images[stem], CORPUS / (stem + ".bin")))
            writers.append(entry)
        elif present[stem] & set(EC_WINDOW_ONLY_ANCHORS):
            ec_window_only.append({
                "stem": stem, "ui": rec.get("ui") or stem, "type": rec["type"],
                "sha256": rec["sha256"],
                "anchors_present": sorted(present[stem]),
                "strong_anchors_present": sorted(set(STRONG) & present[stem]),
                "per_anchor_offsets": anchor_offsets[stem],
            })

    writer_stems = {w["stem"] for w in writers}
    check(writer_stems == EXPECTED_WRITERS,
          "writer set equals the two calibrated VR-controller modules (%s)" % sorted(writer_stems))
    check(PRIOR_NON_WRITER not in writer_stems, "CpuDxe is not classified as a mailbox writer")
    check(not (set(STRONG) & present[PRIOR_NON_WRITER]),
          "CpuDxe carries no strong mailbox anchor")
    for w in writers:
        check(bool(w["helpers"]), "%s: at least one EC transport helper located" % w["stem"])
        check(any(h["full_transport_helper"] for h in w["helpers"]),
              "%s: at least one helper owns both the 0xA20 window and the 0x87 unlock" % w["stem"])
        check(bool(w["call_sites"]), "%s: at least one helper call site with pushed arguments" % w["stem"])
        check(w["rom_reextraction"]["matches_corpus_image"],
              "%s: module re-extracted from the immutable ROM and re-hashed" % w["stem"])
        staged = [s for s in w["call_sites"] if s.get("pushed_register_index") is not None]
        check(bool(staged), "%s: at least one call site exposes a pushed register index" % w["stem"])
        check(all("pushes" in s for s in w["call_sites"]),
              "%s: every call site records its raw pushed arguments" % w["stem"])
        check(len(staged) >= len(w["call_sites"]) // 2,
              "%s: the majority of helper call sites pass an explicit register index" % w["stem"])
        check(any(s.get("staged_value") is not None for s in staged),
              "%s: at least one staged value immediate was recovered" % w["stem"])

    prior = json.loads(PRIOR.read_text())
    prior_re = prior["rom_direct_reextraction"]
    check(set(prior_re) == PRIOR_VR_STEMS, "prior result names the same two VR modules")
    for stem, info in prior_re.items():
        rec = next(r for r in records if r["stem"] == stem)
        check(info["sha256"] == rec["sha256"],
              "prior ROM re-extraction hash for %s equals the census hash" % stem)
    prior_setup = {m["stem"] for m in prior["get_variable_setup_modules"]}
    check(PRIOR_NON_WRITER in prior_setup, "prior result includes the non-writer Setup reader")
    check(PRIOR_VR_STEMS <= prior_setup, "prior result includes both VR modules as Setup readers")
    check(writer_stems == PRIOR_VR_STEMS & prior_setup,
          "new writer set equals the Setup-consuming VR modules of the prior result")

    result = {
        "status": "PASS" if not failed else "FAIL",
        "checks": checks,
        "failed": len(failed),
        "failures": failed,
        "question": "which firmware modules can stage a VR-register write through the "
                    "Super-I/O/EC mailbox window",
        "donor": {"path": str(ROM.relative_to(ROOT)), "size": ROM_SIZE, "sha256": ROM_SHA},
        "corpus": {"path": str(CORPUS.relative_to(ROOT)), "modules": len(records),
                   "census_sha256": CENSUS_SHA, "extractor_sha256": census["extractor_sha256"]},
        "anchor_definitions": [{"name": n, "bytes": h, "note": t} for n, h, t in ANCHORS],
        "strong_anchor_set": STRONG,
        "writers": writers,
        "ec_window_only_modules": ec_window_only,
        "anchor_hit_table": {n: sum(1 for s in present if n in present[s]) for n, _h, _t in ANCHORS},
        "prior_result_crosscheck": {
            "prior_path": str(PRIOR.relative_to(ROOT)),
            "prior_writer_stems": sorted(PRIOR_VR_STEMS),
            "prior_non_writer_stem": PRIOR_NON_WRITER,
            "agree": writer_stems == PRIOR_VR_STEMS,
        },
        "conclusion": "Exactly two of the 233 pinned modules implement the EC-window VR mailbox "
                      "writer; they are the same two modules that consume the Setup fixed-voltage "
                      "fields. No third firmware module in this corpus can stage a VR register "
                      "write through that window. The scanner finds the transport bytes only; it "
                      "does not prove PEI dispatch, mailbox chip identity, PMBus semantics, rail "
                      "identity or any applied voltage.",
        "limitations": [
            "static-analysis over observed bytes only; no dispatch, emulation or hardware evidence",
            "anchor set is calibrated on two known positives and is literal-byte based; a module "
            "implementing the same protocol with different instruction encodings would be missed",
            "register indices are inferred from the pushed arguments of the transport helper",
            "ROM re-extraction uses the FFS-relative 'VZ' TE signature scan; modules inside "
            "compressed firmware volumes are not covered by that path",
        ],
    }
    OUT.write_text(json.dumps(result, indent=1, sort_keys=False) + "\n")
    print("checks=%d failed=%d status=%s" % (checks, len(failed), result["status"]))
    print("writers=%s" % sorted(writer_stems))
    print("ec_window_only=%d modules" % len(ec_window_only))
    print("result=%s" % OUT)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
