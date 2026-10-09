#!/usr/bin/env python3
"""Independent review of the CLV native 1:1:1 recipe: profiles, offsets, endianness, stale artifacts.

Read-only on all inputs. Re-derives the six claimed (QID, AmdSetup offset, option byte) tuples from the
extracted CbsSetupDxe IFR bytes with the existing project parser, audits every declared hash, and re-checks
the endianness/width claims. Writes only its own JSON next to this script.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

CHECKS = []
def chk(name, ok, detail, data=None):
    entry = {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}
    if data is not None:
        entry["data"] = data
    CHECKS.append(entry)
    return ok

INPUTS = [
    "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin",
    "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin",
    "evidence/firmware-audit/20260919-inv-token-consumers/census.json",
    "import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py",
    "evidence/firmware-audit/20260920-df-init-route/menu-CbsSetupDxe.txt",
    "evidence/firmware-audit/20260920-df-init-route/menu-result.json",
    "evidence/firmware-audit/20260920-df-init-route/menu-verify.py",
    "evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json",
    "evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result-H1750-historical.json",
    "evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json.orig-20260920",
    "evidence/firmware-audit/20260920-clv-native-1to1-recipe/SHA256SUMS.final",
    "evidence/firmware-audit/20260920-clv-native-1to1-recipe/SHA256SUMS.final.orig-20260920",
    "evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-result.json",
    "evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review_recipe.py",
    "docs/research/2026-09-20-clv-native-operator-recipe.md",
    "docs/research/2026-09-20-clv-native-1to1-recipe.md",
    "docs/research/2026-09-20-clv-native-menu-1to1-guide.md",
    "docs/research/2026-09-20-clv-uclk-discrimination-guide.md",
    "docs/research/20260920-clv-abl1-r6-3c4-producer-trace.md",
]
PRE = {p: sha(ROOT / p) for p in INPUTS}

# ---------------------------------------------------------------- A. identities
rom_bytes = (ROOT / INPUTS[0]).read_bytes()
chk("donor_rom_size", len(rom_bytes) == 16 * 1024 * 1024, "donor ROM size")
chk("donor_rom_sha256",
    PRE[INPUTS[0]] == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8",
    "donor ROM sha256 matches the recipe baseline")

census = json.loads((ROOT / INPUTS[2]).read_text())
chk("census_input_rom", census.get("sha256") == PRE[INPUTS[0]], "census input is the pinned donor ROM")
rec = [r for r in census["records"] if r.get("ui") == "CbsSetupDxe"][0]
mod_bytes = (ROOT / INPUTS[1]).read_bytes()
chk("module_sha256_matches_census", sha(ROOT / INPUTS[1]) == rec["sha256"] ==
    "7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8",
    "extracted CLV CbsSetupDxe PE32 hash matches the census record and the pinned recipe hash",
    {"size": len(mod_bytes)})
chk("module_not_verbatim_in_rom", rom_bytes.find(mod_bytes) < 0,
    "module bytes are not a verbatim ROM substring (FFS section is compressed); provenance rests on the "
    "recorded extractor, sha256=" + str(census.get("extractor_sha256")))

# ---------------------------------------------------------------- B. IFR re-derivation
spec = importlib.util.spec_from_file_location("ifr", ROOT / INPUTS[3])
parser_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser_mod)

packages = parser_mod.find_packages(mod_bytes)
strings_off, _, strings_len = next(x for x in packages if x[1] == 4)
strings = {k: v.rstrip("\0") for k, v in dict(parser_mod.parse_sibt(mod_bytes[strings_off:strings_off + strings_len])[1]).items()}
forms_off, _, forms_len = next(x for x in packages if x[1] == 2)

WANTED = {0x20F, 0x229, 0x25E, 0x7045, 0x37D, 0x37E, 0x37F}
questions, varstores, current = {}, {}, None
pos = forms_off + 4
end = forms_off + forms_len
while pos < end:
    op = mod_bytes[pos]
    ln = mod_bytes[pos + 1] & 127
    if ln < 2 or pos + ln > end:
        break  # exact AMI forms package tail padding
    body = mod_bytes[pos + 2:pos + ln]
    if op == 2 and len(body) >= 22:  # EFI_IFR_VARSTORE (buffer, raw name)
        vid, size = struct.unpack_from("<H", body, 0)[0], struct.unpack_from("<H", body, 18)[0]
        varstores[vid] = (strings.get(struct.unpack_from("<H", body, 20)[0], ""), size)
    if op == 0x1F and len(body) >= 26:  # EFI_IFR_VARSTORE_EFI (AMITSE: attributes + string-id name)
        vid, size = struct.unpack_from("<H", body, 0)[0], struct.unpack_from("<H", body, 22)[0]
        varstores[vid] = (strings.get(struct.unpack_from("<H", body, 24)[0], ""), size)
    if op in (5, 6, 7):
        prompt, _help, qid, vid, offset, flags = struct.unpack_from("<HHHHHB", body)
        rec_q = {"op": op, "qid": qid, "varstore_id": vid, "offset": offset, "flags": flags,
                 "label": strings.get(prompt, ""), "module_offset": pos, "raw": mod_bytes[pos:pos + ln].hex()}
        if op == 7:
            size = 1 << (body[11] & 3)
            rec_q["bounds"] = [int.from_bytes(body[12 + i * size:12 + (i + 1) * size], "little") for i in range(3)]
            rec_q["numeric_size"] = size
        rec_q["options"] = []
        if qid in WANTED and qid not in questions:
            questions[qid] = rec_q
            current = rec_q
        else:
            current = None
    elif op == 9 and current is not None:  # ONE_OF_OPTION
        sid, fl, typ = struct.unpack_from("<HBB", body)
        size = {0: 1, 1: 2, 2: 4, 3: 8, 4: 1}.get(typ)
        if size:
            current["options"].append({"label": strings.get(sid, ""),
                                       "value": int.from_bytes(body[4:4 + size], "little"),
                                       "size": size, "default": bool(fl & 0x10)})
    elif op == 0x5B and current is not None:  # DEFAULT
        default_id, typ = struct.unpack_from("<HB", body, 0)
        size = {0: 1, 1: 2, 2: 4, 3: 8}.get(typ)
        if size:
            current["default_read_as_le"] = int.from_bytes(body[3:3 + size], "little")
            current["default_read_as_be"] = int.from_bytes(body[3:3 + size], "big")
            current["default_bytes"] = body[3:3 + size].hex()
            current["default_size"] = size
    pos += ln

# The varstore record is not part of the walked FORMS stream; locate it by its GUID in the raw module.
import uuid as _uuid
vs_guid = _uuid.UUID("3A997502-647A-4C82-998E-52EF9486A247").bytes_le
hits, cursor = [], 0
while True:
    h = mod_bytes.find(vs_guid, cursor)
    if h < 0:
        break
    hits.append(h)
    cursor = h + 1
# the varstore record is the occurrence whose following fields decode as id/size/ASCII name
vs_off, vs_id, vs_size, vs_name = -1, None, None, b""
for h in hits:
    cand_id = struct.unpack_from("<H", mod_bytes, h + 16)[0]
    cand_size = struct.unpack_from("<H", mod_bytes, h + 18)[0]
    cand_name = mod_bytes[h + 20:h + 20 + 8]
    if cand_name == b"AmdSetup" and cand_size == 0x08B5:
        vs_off, vs_id, vs_size, vs_name = h, cand_id, cand_size, cand_name
        break
q_vids = {questions[q]["varstore_id"] for q in questions}
chk("varstore_amdsetup",
    vs_off >= 0 and vs_id == 0x5000 and vs_size == 0x08B5 and vs_name.startswith(b"AmdSetup")
    and q_vids == {0x5000},
    "raw varstore record: guid 3A997502-647A-4C82-998E-52EF9486A247 id=0x%X size=0x%X name=%r; all six "
    "questions reference varstore id %s" % (vs_id or 0, vs_size or 0, vs_name.rstrip(b"\x00").decode("latin-1"),
                                            sorted(hex(v) for v in q_vids)),
    {"varstore_module_offset": hex(vs_off), "guid_occurrences": [hex(x) for x in hits], "question_varstore_ids": sorted(hex(v) for v in q_vids)})

chk("all_six_questions_recovered", set(WANTED) <= set(questions),
    "all six claimed questions recovered from raw IFR bytes", {"qids": [hex(q) for q in sorted(questions)]})

CLAIM = {
    0x20F: ("Memory Clock Speed", 0x316, 5),
    0x229: ("UclkDiv1M0", 0x330, 5),
    0x25E: ("Memory P-state", 0x36D, 5),
    0x7045: ("FCLK_DPM", 0x6A3, 5),
    0x37D: ("DF Clock Override Control", 0x703, 5),
    0x37E: ("DF Clock Override", 0x704, 7),
}
for qid, (label, offset, op) in CLAIM.items():
    q = questions[qid]
    ok = q["label"] == label and q["offset"] == offset and q["op"] == op
    chk("offset_%s" % hex(qid), ok,
        "%s: qid 0x%X -> %s+0x%X, opcode 0x%02X (%s)" % (label, qid, varstores.get(q['varstore_id'], ('?',))[0],
                                                          q["offset"], q["op"], q["label"]),
        {"varstore_id": hex(q["varstore_id"]), "flags": hex(q["flags"]), "raw": q["raw"]})

def opt(qid, label):
    q = questions[qid]
    hit = [o for o in q["options"] if o["label"] == label]
    return (hit[0]["value"], hit[0]["size"]) if hit else (None, None)

VALUE_CLAIMS = [
    (0x20F, "1330MHz", 0x1A), (0x20F, "1750MHz", 0x23),
    (0x229, "Enabled", 0x01), (0x25E, "Disabled", 0x00),
    (0x7045, "Disabled", 0x00), (0x37D, "Manual", 0x01),
]
for qid, label, expect in VALUE_CLAIMS:
    got, size = opt(qid, label)
    chk("option_%s_%s" % (hex(qid), label), got == expect and size == 1,
        "0x%X '%s' = 0x%02X (u%d byte)" % (qid, label, got if got is not None else -1, 8 * (size or 1)))

q376 = questions[0x37E]
chk("df_numeric_bounds", q376["bounds"] == [0, 2000, 0],
    "DF Clock Override bounds read from raw bytes: %s" % q376["bounds"],
    {"size_bytes": q376["numeric_size"]})
chk("df_numeric_default_le", q376.get("default_bytes") == "e803" and q376.get("default_read_as_le") == 1000
    and q376.get("default_read_as_be") == 59395 and q376.get("default_size") == 2,
    "DF Clock Override default bytes %s -> LE %s (in 0..2000) / BE %s (out of range)"
    % (q376.get("default_bytes"), q376.get("default_read_as_le"), q376.get("default_read_as_be")))

# width audit from neighbour offsets inside the same varstore
neigh = [(0x20F, 0x210), (0x229, 0x22A), (0x25E, 0x261), (0x7045, 0x7046), (0x37D, 0x37E), (0x37E, 0x37F)]
widths = {}
txt = (ROOT / INPUTS[4]).read_text()
import re as _re
for a, b in neigh:
    oa = next(int(m, 16) for m in _re.findall(r"qid=0x%x var=AmdSetup\+0x([0-9a-f]+)" % a, txt))
    ob = next(int(m, 16) for m in _re.findall(r"qid=0x%x var=AmdSetup\+0x([0-9a-f]+)" % b, txt))
    widths["0x%X" % a] = ob - oa
chk("oneof_width_u8", all(widths["0x%X" % q] == 1 for q in (0x20F, 0x229, 0x25E, 0x7045, 0x37D)),
    "ONE_OF option fields occupy 1 byte (neighbour offset deltas %s)" % widths)
chk("df_override_width_u16", widths["0x37E"] == 2,
    "DF Clock Override occupies 2 bytes: +0x704 -> next question +0x706")

# ---------------------------------------------------------------- C. claim cross-check
machine = json.loads((ROOT / INPUTS[7]).read_text())
settings = {s["name"]: s for s in machine["settings"]}
chk("machine_profile_h1330", machine.get("test_point") == "H1330-native-help" and machine.get("no_voltage") is True,
    "current machine result profile = %s (no_voltage=%s)" % (machine.get("test_point"), machine.get("no_voltage")))
mismatch = []
for qid, (label, offset, _op) in CLAIM.items():
    s = settings.get(label)
    if s is None:
        mismatch.append(label + ":missing")
        continue
    if int(s["offset"], 16) != offset or int(s["qid"], 16) != qid:
        mismatch.append(label + ":offset/qid")
chk("machine_offsets_match_ifr", not mismatch,
    "recipe-result.json qid/offset pairs match the raw IFR records" + (" mismatches=%s" % mismatch if mismatch else ""))

df_val = settings["DF Clock Override"]["value"]
m = _re.search(r"(\d+) / bytes ([0-9a-f ]+) LE", df_val)
dec = int(m.group(1)); raw = bytes.fromhex(m.group(2).replace(" ", ""))
chk("df_1330_encoding", dec == 1330 and int.from_bytes(raw, "little") == 1330 and raw == b"\x32\x05",
    "current profile DF value '%s' -> LE 0x%04X = %d" % (df_val, int.from_bytes(raw, "little"), int.from_bytes(raw, "little")))

hist = json.loads((ROOT / INPUTS[8]).read_text())
h = {s["name"]: s for s in hist["settings"]}
m2 = _re.search(r"(\d+) / bytes ([0-9A-Fa-f ]+) LE", h["DF Clock Override"]["value"])
dec2 = int(m2.group(1)); raw2 = bytes.fromhex(m2.group(2).replace(" ", ""))
chk("df_1750_encoding", dec2 == 1750 and int.from_bytes(raw2, "little") == 1750,
    "historical H1750 DF value '%s' -> LE 0x%04X = %d" % (h["DF Clock Override"]["value"],
                                                          int.from_bytes(raw2, "little"), int.from_bytes(raw2, "little")))
chk("historical_profile_kept", hist.get("test_point") == "H1750-native-help"
    and machine["historical_reference"]["file"] == "recipe-result-H1750-historical.json",
    "H1750 record preserved and labelled as the superseded historical profile")
chk("historical_file_identical_to_orig", sha(ROOT / INPUTS[8]) == sha(ROOT / INPUTS[9]) ==
    "e4a2c4231070d83829f14c65087cd1ec3aadd20a00cd4b8ef2872de08849477d",
    "recipe-result-H1750-historical.json is byte-identical to the pre-correction recipe-result.json")

op_text = (ROOT / INPUTS[14]).read_text()
chk("correction_wording_present", "lower historical comparison point; no safety/stress inference" in op_text
    and "recommends the deterministic 1330 MHz" in machine.get("recommendation_basis", ""),
    "review wording correction applied and machine result names the current H1330 recommendation")
h1750_doc = (ROOT / INPUTS[15]).read_text()
chk("h1750_doc_marks_hypothesis", "H1750" in h1750_doc and "hypothesis" in h1750_doc,
    "the 1750 report self-labels as a diagnostic hypothesis rather than a validated profile")

# ---------------------------------------------------------------- D. stale-artifact audit
def parse_sums(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        h, _, name = line.partition("  ")
        out[name.strip()] = h.strip()
    return out

base = ROOT / "evidence/firmware-audit/20260920-clv-native-1to1-recipe"
declared = parse_sums(base / "SHA256SUMS.final")
bad = [n for n, h in declared.items() if not (base / n).resolve().exists() or sha((base / n).resolve()) != h]
chk("manifest_SHA256SUMS.final", not bad,
    "%d declared hashes verified against current bytes on disk" % len(declared) + (" stale=%s" % bad if bad else ""))
# The pre-correction manifest is a historical record: it must still describe the preserved pre-correction
# siblings, not the corrected current file.
declared_orig = parse_sums(base / "SHA256SUMS.final.orig-20260920")
resolved, bad_orig = {}, []
for name, h in declared_orig.items():
    cur = (base / name).resolve()
    sib = Path(str(cur) + ".orig-20260920")
    if cur.exists() and sha(cur) == h:
        resolved[name] = "current"
    elif sib.exists() and sha(sib) == h:
        resolved[name] = "orig-sibling"
    else:
        bad_orig.append(name)
chk("manifest_SHA256SUMS.final.orig-20260920", not bad_orig,
    "pre-correction manifest verified against preserved siblings: " + json.dumps(resolved)
    + (" stale=%s" % bad_orig if bad_orig else ""))

rv = json.loads((ROOT / INPUTS[12]).read_text())
bad = [p for p, meta in rv.get("inputs", {}).items() if sha(ROOT / p) != meta["sha256"]]
chk("review_result_inputs_fresh", not bad, "review-result.json inputs still match disk" + (" stale=%s" % bad if bad else ""))
chk("menu_result_unchanged", sha(ROOT / INPUTS[5]) == "6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a",
    "menu-result.json still matches the hash declared in recipe-result.json before/after the fresh verifier run")
art = machine["artifacts"]
missing = [v for v in art.values() if not Path(v).exists()]
chk("artifact_paths_exist", not missing, "every path cited by recipe-result.json exists", {"artifacts": art})

# ---------------------------------------------------------------- report
POST = {p: sha(ROOT / p) for p in INPUTS}
changed = [p for p in INPUTS if PRE[p] != POST[p]]
chk("inputs_unmodified", not changed, "all %d inputs unchanged by this review" % len(INPUTS)
    + (" changed=%s" % changed if changed else ""))

status = "PASS" if all(c["status"] == "PASS" for c in CHECKS) else "FAIL"
result = {
    "status": status,
    "checks": len(CHECKS),
    "failed": sum(1 for c in CHECKS if c["status"] == "FAIL"),
    "checks_detail": CHECKS,
    "scope": ("profiles H1330/H1750, AmdSetup offsets, endianness and stale-artifact audit; "
              "strategy-only static review; no ROM/NVRAM/hardware/register action"),
    "inputs": {p: {"size": (ROOT / p).stat().st_size, "sha256": PRE[p]} for p in INPUTS},
    "limits": [
        "Bytes for the six fields come from the extracted CLV CbsSetupDxe PE32 (sha256 7ff717d5...); the module "
        "is not a verbatim ROM substring because the FFS section is compressed, so provenance rests on the "
        "recorded extractor hash, not on a byte-substring match.",
        "IFR record type/option bytes are static requests; nothing here shows that firmware applies them, that "
        "NVRAM persists them, or that any clock ratio becomes 1:1:1.",
        "UclkDiv1M0 'Enabled' remains an undecoded enum byte; Memory Clock Speed values are option-table indices, "
        "not a MHz/50 arithmetic scaling.",
    ],
}
(OUT / "native-recipe-review-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": status, "checks": result["checks"], "failed": result["failed"],
                  "failures": [c["name"] for c in CHECKS if c["status"] == "FAIL"]}))
