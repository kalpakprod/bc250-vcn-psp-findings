#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smn_lock_probe.py — проверка живого вопроса из 04-smn-write-protection-hypothesis.md:
latch-ятся ли донор-записи в DF-окна из SMU-контекста (Q3 0x2B/0x2C), или их
молча дропает DF hardware-lock (LockDFReg 0x1b после boot-гаскета).

ЗАПУСК НА ПЛАТЕ (root), из корня репо bc250-smu-unlock (рядом с unlock.py
и пакетом bc250_smu):

    python3 smn_lock_probe.py                 # Phase A: только ЧТЕНИЯ (безопасно)
    python3 smn_lock_probe.py --phase-b       # + одна аддитивная запись-проба

Phase A (по умолчанию) — безопасный read-only обзор всей дельта-поверхности:
банк-12, DF-окна 0x03a2/0x0322/0x03d2, VCN_SEG 0x03e8, NBIF 0x1c7xx, NBIO 0x1f8xx.

Phase B (только с --phase-b) — одна запись: 0x03a2011c 0x87ff -> 0x107ff
(ДОБАВЛЯЕТ бит-12 = банк-12 в DF-окно; ничего не снимает) + readback:
  LATCHED  — окно записываемо в рантайме => runtime-b2a жизнеспособен
  DROPPED  — запись дропнута (hardware-lock / fabric-фильтр) => runtime-путь
             для окон мёртв; только boot-time (лестница прошивки / A2)
  WEDGED   — Q3-таймаут: SMU-почта повешена; нужен цикл питания

Правила останова (W-каталог, analysis-psp/01 §7):
  - ЛЮБОЙ таймаут => немедленный STOP всего прогона (дальнейшие чтения
    бессмыслены, почта мертва). Восстановление — холодный цикл питания.
  - Здесь НЕТ MMIO-чтений (W2), нет записей в 0x1F8xx (W3), нет PCI 0xB8/0xBC (W4/W6).
  - Порядок чтений: от проверенных (банк-12, 26.08) к рискованным
    (0x03d2xxxx читается ПОСЛЕДНИМ — на Robin семейство отсутствует в гаскете,
    возможно не размечено => риск W5-класса на dead-регион).

Phase B НЕ читает VCN MMIO и НЕ пишет ничего кроме 0x03a2011c: если LATCHED,
следующий шаг — отдельно replay_vcn_unlock.py --level b2a (ветка psp-vcn-unlock)
с save-first MMIO-пробой в дочернем процессе.
"""

import argparse
import json
import os
import sys
import time

# --- расположение библиотеки: этот скрипт лежит рядом с bc250_smu/ и unlock.py
HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (HERE, os.getcwd()):
    if os.path.isdir(os.path.join(cand, "bc250_smu")):
        if cand not in sys.path:
            sys.path.insert(0, cand)
        break
else:
    sys.exit("bc250_smu package not found: run from the bc250-smu-unlock repo root "
             "or copy this script next to bc250_smu/")

from bc250_smu import Bc250Smu                      # noqa: E402
from bc250_smu.errors import SmuError, SmuTimeout    # noqa: E402

# ---------------------------------------------------------------------------
# Phase A: read-only survey. Порядок = от проверенного к рискованному.
# 03.09.2026 (полевой результат, см. 04 §10): чтение 0x0900c234 на холодном
# боке CachyOS с загруженным amdgpu ГЛОБАЛЬНО вешает SMU (вплоть до интерфейса
# amdgpu) — банк-12 доступен только в некогда-программированном/запитанном
# состоянии (W5-класс). Поэтому банк-12 по умолчанию ИСКЛЮЧЁН и читается
# ПОСЛЕДНИМ, только с --with-bank12.
# (addr, метка, robin-ожидание, donor-ожидание, примечание)
SURVEY = [
    # 0) контроль: SMU PM-регион — этот адрес читается пробой unlock-а в том же
    #    прогоне (PROBE_ADDR); если контроль OK, а следующий за ним DF-адрес
    #    вешает SMU — клин специфичен для DF-пространства, а не для 0x2A вообще
    (0x0005A870, "control: SMU PM (unlock probe)", "0x77 (сток) / 0xFF", "-",
     "контроль живости 0x2A вне DF-пространства"),
    # 1) DF-окна 0x03a2 (гаскет Robin: 0x87ff/0xffff0000; донор: 0x107ff/0x10fff)
    (0x03A2011C, "DF window 0x03a2 11c",   "0x000087ff", "0x000107ff", "бит-12 (банк-12) у Robin ОТСУТСТВУЕТ"),
    (0x03A20120, "DF window 0x03a2 120",   "0xffff0000", "0xffff0000?", "Robin и донор совпадают? (b2a не пишет)"),
    (0x03A20124, "DF window 0x03a2 124",   "? (Robin не пишет)", "0x00010fff", "b2a пишет"),
    # 2) DF-окна 0x0322 (гаскет Robin varA 0x8000/0x8707; TOS-копия varB 0x80ff/0x87ff; донор 0x10000/0x10707/0x101ff)
    (0x0322011C, "DF window 0x0322 11c",   "0x00008000 (A) / 0x000080ff (B=TOS)", "0x00010000", "b2b пишет"),
    (0x03220124, "DF window 0x0322 124",   "0x00008707 (A) / 0x000087ff (B)",      "0x00010707", "b2b пишет"),
    (0x0322012C, "DF window 0x0322 12c",   "0x00008707 (A)", "0x000101ff", "b2b пишет"),
    # 3) VCN_SEG binding (группа 0x210; Robin оставляет значения ОТСУТСТВУЮЩИМИ)
    (0x03E810,   "VCN_SEG enable",         "0/нет (Robin пропускает)", "0x00000006", "b2a пишет"),
    (0x03E814,   "VCN_SEG binding value",  "0/нет (Robin пропускает)", "0x2544c382", "b2a пишет"),
    # 4) NBIF маршруты 0x1c7xx (Robin не пишет; донор пишет)
    (0x01C760,   "NBIF route 0x1c760",     "нет (Robin не пишет)", "0xff400000", "b2a пишет"),
    (0x01C764,   "NBIF route 0x1c764",     "нет",                   "0xff400000", "b2a пишет"),
    (0x01C780,   "NBIF route 0x1c780",     "нет",                   "0x00000000", "b2a пишет"),
    (0x01C784,   "NBIF route 0x1c784",     "нет",                   "0x00000000", "b2a пишет"),
    (0x01C788,   "NBIF route 0x1c788",     "нет",                   "0x000000ff", "b2a пишет"),
    (0x01C78C,   "NBIF route 0x1c78c",     "нет",                   "0x00000107", "b2a пишет (v3-builder тоже)"),
    # 5) NBIO VCN route
    (0x01F820,   "NBIO VCN route 0x1f820", "?", "0x00185103", "b2a пишет"),
    (0x01F8A4,   "NBIO 0x1f8a4",           "?", "0x0000000b -> 0", "b2a пишет дважды"),
    # 6) 0x03d2-зеркало — ПОСЛЕДНИМ в основном обходе: у Robin семейство
    #    отсутствует, регион возможно не размечен (риск W5: read abort на
    #    dead-регионе)
    (0x03D2011C, "DF mirror 0x03d2 11c",   "нет (Robin не пишет)", "0x000107ff", "b2a пишет"),
    (0x03D20124, "DF mirror 0x03d2 124",   "нет (Robin не пишет)", "0x00010fff", "b2a пишет"),
]

# банк-12: только с --with-bank12, добавляется В КОНЕЦ обхода (03.09.2026:
# чтение 0x0900c234 на холодном боке вешает SMU; см. заголовок SURVEY)
SURVEY_BANK12 = [
    (0x0900C234, "bank12 enable/commit",   "0 (не программился) / 1 (осталось с 26.08)", "1", "234: 0=program 1=commit; W5-риск на холодном боке!"),
    (0x0900CB80, "bank12 enable bitmap",   "0",                  "0xff", "изоляционный зажим"),
    (0x0900C910, "bank12 cfg",             "donor 0x01000003 (писали 26.08)", "0x01000003", "g0x201"),
    (0x0900C914, "bank12 cfg",             "donor 0 (писали 26.08)", "0", "g0x201/хвост 0x280"),
    (0x0900C930, "bank12 cfg 0x36",        "donor 0x36 (писали 26.08)", "0x36", "g0x201/хвост 0x280"),
]

# Phase B: единственная запись-проба (аддитивная: 0x87ff | 0x1000)
PB_ADDR = 0x03A2011C
PB_OLD = 0x000087FF     # ожидаемое Robin-значение (предусловие Phase B)
PB_NEW = 0x000107FF     # донор: +бит-12 (банк-12 в окне)


def fmt(x):
    return "0x%08x" % x if isinstance(x, int) else str(x)


def _make_smu(args):
    """Конструктор, устойчивый к версии библиотеки на плате
    (board-копия может принимать use_flock и не иметь alive())."""
    try:
        return Bc250Smu(bdf=args.bdf, timeout=args.timeout)
    except TypeError:
        return Bc250Smu()


def _smu_alive(smu) -> bool:
    for name in ("alive", "check_test_message"):
        fn = getattr(smu, name, None)
        if fn is not None:
            try:
                return bool(fn())
            except Exception:
                return False
    try:
        smu.test_message(0x5EED0000)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--bdf", default="0000:00:00.0")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--phase-b", action="store_true",
                    help="разрешить ОДНУ запись 0x03a2011c 0x87ff->0x107ff + readback")
    ap.add_argument("--with-bank12", action="store_true",
                    help="добавить в КОНЕЦ обхода чтения банк-12 (0x0900cxxx): "
                         "03.09.2026 на холодном боке CachyOS/amdgpu чтение 0x0900c234 "
                         "ГЛОБАЛЬНО вешает SMU — только с доступным циклом питания")
    ap.add_argument("--no-unlock", action="store_true",
                    help="не запускать VULN-A unlock (требует, что гейт уже открыт)")
    ap.add_argument("--out", default=None, help="путь JSON-лога (по умолчанию smn_lock_probe_<ts>.json)")
    args = ap.parse_args()

    log = {"argv": sys.argv, "bdf": args.bdf, "with_bank12": bool(args.with_bank12),
           "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "phase_a": [], "phase_b": None, "verdict": None}
    out_path = args.out or os.path.join(HERE, "smn_lock_probe_%s.json" % time.strftime("%Y%m%d_%H%M%S"))

    print("== smn_lock_probe: Phase A (read-only) ==")
    smu = _make_smu(args)
    try:
        if not _smu_alive(smu):
            print("FATAL: SMU test message failed (alive()==False) — ничего не делаем")
            return 3
        print("SMU alive: OK")

        if not smu.secure_access_enabled():
            if args.no_unlock:
                print("FATAL: secure cluster закрыт, --no-unlock задан — выходим")
                return 3
            print("secure cluster закрыт -> VULN-A unlock (Q2 0x23 ring overflow)...")
            import unlock as _unlock_mod
            _unlock_mod.smu = smu  # PoC-хелперы (overwrite_tr_table_ptr) берут глобал smu
            _unlock_mod.unlock(smu)
        if not smu.secure_access_enabled():
            print("FATAL: unlock не открыл гейт — выходим без записей")
            return 3
        print("secure access: OPEN")

        # ---------------- Phase A ----------------
        survey = list(SURVEY)
        if args.with_bank12:
            survey += SURVEY_BANK12
            print("банк-12 ВКЛЮЧЁН в обход (последним, W5-риск на холодном боке)")
        else:
            print("банк-12 исключён из обхода (по умолчанию; --with-bank12 чтобы добавить)")
        wedge = False
        for addr, label, exp_robin, exp_donor, note in survey:
            rec = {"addr": fmt(addr), "label": label,
                   "expect_robin": exp_robin, "expect_donor": exp_donor, "note": note}
            try:
                v = smu.smn_read32(addr)
                rec["value"] = fmt(v)
                print("  %-13s %-22s = %s   (robin: %s | donor: %s)"
                      % (fmt(addr), label, fmt(v), exp_robin, exp_donor))
            except SmuTimeout as e:
                rec["error"] = "TIMEOUT/SMU-WEDGED"
                print("  %-13s %-22s !! %s" % (fmt(addr), label, e))
                log["phase_a"].append(rec)
                wedge = True
                break          # правило останова: почта мертва, дальше не читаем
            except SmuError as e:
                rec["error"] = "REJECTED %s" % e
                print("  %-13s %-22s ?? rejected: %s" % (fmt(addr), label, e))
            log["phase_a"].append(rec)

        if wedge:
            log["verdict"] = "WEDGED (Phase A read) — холодный цикл питания; " \
                             "записи не выполнялись"
            print("\nVERDICT: WEDGED на чтении — SMU-почта повешена. "
                  "Холодный цикл питания. Записей НЕ было.")
            return 2

        # ---------------- Phase B ----------------
        if args.phase_b:
            print("\n== Phase B: единственная запись %s <- %s (аддитивно к %s) =="
                  % (fmt(PB_ADDR), fmt(PB_NEW), fmt(PB_OLD)))
            cur = smu.smn_read32(PB_ADDR)
            if cur != PB_OLD:
                log["phase_b"] = {"precheck": "abort", "value": fmt(cur)}
                log["verdict"] = "PHASE-B-ABORT: %s == %s, ожидалось %s — не пишем" \
                                 % (fmt(PB_ADDR), fmt(cur), fmt(PB_OLD))
                print("ABORT: текущее значение %s != %s (проверь Phase A) — запись отменена"
                      % (fmt(cur), fmt(PB_OLD)))
            else:
                print("предусловие выполнено (%s == %s) -> пишем" % (fmt(cur), fmt(PB_OLD)))
                pb = {"addr": fmt(PB_ADDR), "wrote": fmt(PB_NEW)}
                try:
                    smu.smn_write32(PB_ADDR, PB_NEW)
                    time.sleep(0.05)
                    back = smu.smn_read32(PB_ADDR)
                    pb["readback"] = fmt(back)
                    if back == PB_NEW:
                        pb["result"] = "LATCHED"
                        log["verdict"] = ("LATCHED: DF-окно записываемо из SMU-контекста в "
                                          "рантайме. Runtime-b2a жизнеспособен. Откат при "
                                          "желании: smn_write32(0x03a2011c, 0x87ff). Следующий "
                                          "шаг — replay_vcn_unlock.py --level b2a.")
                    elif back == PB_OLD:
                        pb["result"] = "DROPPED"
                        log["verdict"] = ("DROPPED: запись принята почтой, но не зафиксирована "
                                          "— DF hardware-lock (LockDFReg 0x1b) или fabric-"
                                          "фильтр. Runtime-путь для окон МЁРТВ; только "
                                          "boot-time (лестница прошивки / A2).")
                    else:
                        pb["result"] = "UNEXPECTED"
                        log["verdict"] = "UNEXPECTED readback %s — сними дамп и не продолжай" % fmt(back)
                    print("readback: %s -> %s" % (fmt(PB_NEW), fmt(back)))
                except SmuTimeout as e:
                    pb["result"] = "WEDGED"
                    log["verdict"] = ("WEDGED (Phase B write): %s. Холодный цикл питания. "
                                      "Совпадает с Артём-классом (P3.00 Q3 0x2C на 0x0900c234)."
                                      % e)
                    print("!! WEDGED: %s" % e)
                log["phase_b"] = pb
        else:
            log["verdict"] = "PHASE-A-ONLY (без --phase-b записей не было)"
    finally:
        smu.close()
        log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(out_path, "w") as f:
            json.dump(log, f, indent=1, ensure_ascii=False)
        print("\nJSON-лог: %s" % out_path)

    print("VERDICT: %s" % log["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
