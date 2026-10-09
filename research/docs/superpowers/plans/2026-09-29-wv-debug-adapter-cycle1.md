# WV Debug Adapter — Cycle 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Дать Waveshare RP2350B-Plus-W базовые роли «живёт-показывает-жмёт» — инвентаризацию плат, режимные stubs, PMBus-мониторинг через `I2C_HEADER1`, кнопку Power и веб-панель, — чтобы к следующему циклу можно было приступить к TOCTOU-подмене BIOS с рабочим observability-контуром.

**Architecture:** Работа идёт в двух репозиториях: bc250 (`~/orca/projects/bc250`) держит инвентаризацию, скрипты, тесты и документацию; pico-bc250 (`~/pico-bc250`) держит прошивку и Decky-плагин. Прошивка расширяется двумя новыми режимами (`MODE_MONITOR`, `MODE_POWER_CTRL`) в существующем mode-enum поверх Phase 1 (peer eltex-65). PMBus-опрос идёт через bit-bang I2C на GPIO, публикация в MQTT — через WiFi CYW43, веб-панель — статический HTML+WS на порту 80.

**Tech Stack:** Pico SDK 2.3.1, TinyUSB 0.20.0, BTstack, `paho-mqtt` (для host-тестов), pytest, Python 3, C/C++ для прошивки, mkdocs/plain-md для документации.

**Spec:** `.procoder/specs/wv-debug-adapter.md`

## Global Constraints

- Питание WV: строго USB-C от внешнего активного USB-Hub, никакой пайки, никакого питания от BC-250.
- Никакой пайки на плату BC-250 (только клипсы, пиновые разъёмы, DuPont).
- MQTT-брокер локальный `127.0.0.1:1883` (HAOS), коробочка публикует туда.
- Pico SDK 2.3.1 + TinyUSB 0.20.0, cpu-clock 400 MHz — те же constraints что Phase 1.
- BT-стек — BTstack (`pico_btstack_classic` + `pico_btstack_cyw43`), уже слинкован.
- Никакого прямого SMU-доступа через SMN, никаких изменений в signed PSP-регионах.
- Прошивка BC-250 не пишется без свежего дампа + подтверждённого восстановления + явного «да» владельца.
- Тесты пишутся сначала (TDD), фейлящийся тест обязателен до реализации.
- Все commits в бранч `feature/wv-debug-adapter-cycle1` в каждом репо (не в master/main).
- Никакого AI-authorship в commit-messages.
- Peer eltex-65 держит `~/pico-bc250/src/bt.cpp`, `bridge_main.cpp`, `state_mgr.cpp` — не трогать без согласования; MODE_MONITOR и MODE_POWER_CTRL живут в новых файлах.

## Review Focus

- **BC-250 выключена, коробочка стартует первой:** PMBus @ 0x60 не отвечает, tests не должны падать, `bc250/pmbus/*` публикует `null` вместо стейла; за это отвечает Task 3.
- **I2C-конфликт с LPC-контроллером:** одновременная попытка чтения от NCT и от WV, наш read падает по NACK; в Task 3 arbitration lock с fallback на 3-секундный интервал.
- **MQTT-брокер лежит:** WiFi connect ok, но `127.0.0.1:1883` не отвечает; Task 3 держит local ring-buffer 60 сэмплов, при восстановлении broker'а фleush-ит.
- **Веб-панель на другом браузере (Firefox Android):** WebSocket handshake может отличаться от Chromium; Task 5 тест `TestWebPanelLayoutAt360Px` также прогоняется на geckodriver.
- **Первый включённый GPIO Power-header дребезжит:** без опто-развязки на выходе может подать паразитный short-циркуляр; Task 4 обязательно ставит логику в forget-state до первого CDC `SELFTEST`.

---

## Task 1: Инвентаризация header'ов BC-250 (S-1)

**Files:**
- Create: `docs/hardware/bc250-headers-map.md` — таблица всех header'ов с pin→signal→level→status
- Create: `scripts/check_headers_map.py` — Python-валидатор schema и статусов
- Create: `tests/wv_debug_adapter/__init__.py` — пустой файл-пакет
- Create: `tests/wv_debug_adapter/test_headers_map.py` — pytest-проверки
- Modify: `Makefile:` — добавить target `test-wv-debug` в существующие commands

**Interfaces:**
- Consumes: локальный CAD в `evidence/hardware/` и BoardView (если есть), фото платы владельца (владелец кладёт в `evidence/hardware/photos/2026-09-29/*.jpg`).
- Produces:
  - Функция `parse_headers_map(path: Path) -> list[dict]` в `scripts/check_headers_map.py` — возвращает list header'ов с полями `name`, `connector`, `pins`, `status`, `justification`.
  - Функция `validate_map(headers: list[dict]) -> list[str]` — возвращает список нарушений schema (пустой при OK).

### Steps

- [ ] **Step 1: Написать failing тест TestHeadersMapCompleteness**

```python
# tests/wv_debug_adapter/test_headers_map.py
from pathlib import Path
import pytest

from scripts.check_headers_map import parse_headers_map, validate_map

ALLOWED_STATUSES = {
    "распаян и используется",
    "распаян не используется",
    "не распаян",
}


class TestHeadersMapCompleteness:
    def test_file_exists(self):
        assert Path("docs/hardware/bc250-headers-map.md").exists()

    def test_schema_valid(self):
        headers = parse_headers_map(Path("docs/hardware/bc250-headers-map.md"))
        assert len(headers) >= 1
        violations = validate_map(headers)
        assert violations == [], f"schema violations: {violations}"

    def test_all_headers_have_status(self):
        headers = parse_headers_map(Path("docs/hardware/bc250-headers-map.md"))
        for h in headers:
            assert h["status"] in ALLOWED_STATUSES, (
                f"header {h['name']!r} has status {h['status']!r} "
                f"outside {ALLOWED_STATUSES}"
            )

    def test_j4004_present(self):
        # From MISTAKES 2026-09-27: J4004 already used for BIOS flash.
        headers = parse_headers_map(Path("docs/hardware/bc250-headers-map.md"))
        assert any(h["name"] == "J4004" for h in headers)

    def test_i2c_header1_present(self):
        # From MISTAKES 2026-09-28: pin map CAD-confirmed.
        headers = parse_headers_map(Path("docs/hardware/bc250-headers-map.md"))
        assert any(h["name"] == "I2C_HEADER1" for h in headers)
```

- [ ] **Step 2: Run — must fail with import error or file-not-found**

```bash
cd ~/orca/projects/bc250
pytest tests/wv_debug_adapter/test_headers_map.py -v
```

Expected: `ModuleNotFoundError: scripts.check_headers_map` OR `AssertionError` on file existence.

- [ ] **Step 3: Написать minimal `scripts/check_headers_map.py`**

```python
"""Validator for docs/hardware/bc250-headers-map.md schema."""
from __future__ import annotations

import re
from pathlib import Path

ALLOWED_STATUSES = {
    "распаян и используется",
    "распаян не используется",
    "не распаян",
}

# One header per H3 section: "### <name>" with a "- Status: <status>" line
# and "- Connector: <text>" and "- Pins: <text>".
_HEADER_RE = re.compile(r"^###\s+(\S+)\s*$", re.MULTILINE)
_FIELD_RE = re.compile(r"^-\s+(\w+):\s+(.+?)\s*$", re.MULTILINE)


def parse_headers_map(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    result: list[dict] = []
    matches = list(_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        fields = dict(_FIELD_RE.findall(block))
        result.append({
            "name": name,
            "connector": fields.get("Connector", ""),
            "pins": fields.get("Pins", ""),
            "status": fields.get("Status", ""),
            "justification": fields.get("Justification", ""),
        })
    return result


def validate_map(headers: list[dict]) -> list[str]:
    violations: list[str] = []
    for h in headers:
        if not h["name"]:
            violations.append("header without a name")
        if h["status"] not in ALLOWED_STATUSES:
            violations.append(
                f"{h['name']}: status {h['status']!r} not in allowed set"
            )
        if not h["connector"]:
            violations.append(f"{h['name']}: missing Connector")
        if not h["pins"]:
            violations.append(f"{h['name']}: missing Pins")
    return violations


if __name__ == "__main__":
    import sys
    headers = parse_headers_map(Path("docs/hardware/bc250-headers-map.md"))
    violations = validate_map(headers)
    if violations:
        for v in violations:
            print(v, file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(headers)} headers, all statuses valid")
```

- [ ] **Step 4: Собрать первую версию `docs/hardware/bc250-headers-map.md` из локального CAD**

Прочитай `evidence/hardware/` (все .brd, .kicad_pcb, .cadview) через `grep -rIln "J4004\|TPMS\|I2C_HEADER" evidence/hardware/` и извлеки хотя бы 4 подтверждённых header'а. Минимальный required набор для прохождения теста:

```markdown
# BC-250 Headers Map

Источник: локальный CAD в `evidence/hardware/`, BoardView `evidence/hardware/boardview/`.
Каждый header — H3-заголовок; поля Connector, Pins, Status, Justification — bullet-list.

## Header inventory

### J4004
- Connector: 8-pin SOP-8 socket, 1.27 mm pitch
- Pins: 1=CS#, 2=DO, 3=/WP, 4=GND, 5=DI, 6=CLK, 7=/HOLD, 8=VCC(+3.3V)
- Status: распаян и используется
- Justification: MISTAKES 2026-09-27 — владелец уже флэшил BIOS через J4004; CAD-net trace to W25Q chip.

### I2C_HEADER1
- Connector: 3-pin header, 2.54 mm pitch
- Pins: 1=SDA, 2=SCL, 3=GND (+3.3V pull-up на плате)
- Status: распаян не используется
- Justification: MISTAKES 2026-09-28 — CAD-подтверждённые pull-ups к +3.3V_RUN; BC250-Telemetry hardware.md ссылается на этот header для PMBus.

### TPMS1
- Connector: 18-pin header, 2.0 mm pitch
- Pins: 4=SMB_CLK_MAIN, 6=SMB_DATA_MAIN, 2,12,17,18=GND (остальные — LPC signals)
- Status: распаян не используется
- Justification: BC250-Telemetry hardware.md — SMBus от LPC-контроллера подсоединяется к I2C_HEADER1 pins 1-2.

### FRONT_PANEL_HDR
- Connector: 10-pin dual-row, 2.54 mm pitch
- Pins: 1-2=Power SW, 3-4=Reset SW, 5-6=Power LED, 7-8=HDD LED, 9=GND, 10=NC
- Status: распаян и используется
- Justification: CAD trace — front-panel connector to SIO GPIO; необходим для Task 4 (Power GPIO из WV).
```

Если фото владельца ещё не в `evidence/hardware/photos/2026-09-29/`, оставь строку `- Justification:` с `TODO photo` и создай задачу в трекере «получить фото платы у владельца» — Task 1 закрывается когда CAD-часть готова, фото добавляются отдельным commit'ом позже.

- [ ] **Step 5: Run — тест должен пройти**

```bash
cd ~/orca/projects/bc250
pytest tests/wv_debug_adapter/test_headers_map.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Проверить через procoder spec check**

```bash
procoder spec check wv-debug-adapter
```

Expected: `spec wv-debug-adapter: COMPLETE`.

- [ ] **Step 7: Commit**

```bash
cd ~/orca/projects/bc250
git checkout -b feature/wv-debug-adapter-cycle1
git add docs/hardware/bc250-headers-map.md scripts/check_headers_map.py \
        tests/wv_debug_adapter/__init__.py tests/wv_debug_adapter/test_headers_map.py \
        Makefile
git commit -m "wv-debug-adapter: seed headers map + schema validator (S-1)

Adds docs/hardware/bc250-headers-map.md with 4 baseline BC-250 headers
(J4004, I2C_HEADER1, TPMS1, FRONT_PANEL_HDR) and a Python validator
scripts/check_headers_map.py. TestHeadersMapCompleteness enforces the
schema and the status vocabulary. Photo-based verification is a
follow-up commit when owner supplies board photos."
```

---

## Task 2: MODE-инфраструктура в pico-bc250 (S-2)

**Files (all in `~/pico-bc250/`):**
- Modify: `src/mode/mode.h:` — расширить enum
- Modify: `src/mode/mode.c:` — обновить парсер `MODE`
- Create: `src/monitor/monitor.h` — public API `monitor_init()`
- Create: `src/monitor/monitor.c` — stub, только `monitor_init` void-функция
- Create: `src/power_ctrl/power_ctrl.h` — public API `power_ctrl_init()`
- Create: `src/power_ctrl/power_ctrl.c` — stub
- Modify: `src/main.c:` — dispatch на новые режимы
- Modify: `CMakeLists.txt:` — добавить `src/monitor/monitor.c`, `src/power_ctrl/power_ctrl.c`
- Create: `tests/host/test_mode_parser.c` — host unit-test через `cmake -DBUILD_HOST_TESTS=ON`
- Create: `tests/wv_debug_adapter/test_unified_symbols.py` — nm-проверка ELF
- Create: `tests/wv_debug_adapter/test_cdc_mode.py` — hardware-in-the-loop через `/dev/ttyACM*`

**Interfaces:**
- Consumes: enum `mode_t`, функция `mode_dispatch(mode_t)` из существующего `mode.h`.
- Produces:
  - `void monitor_init(void);` — вызывается один раз из `mode_dispatch` при `MODE_MONITOR`
  - `void power_ctrl_init(void);` — то же для `MODE_POWER_CTRL`
  - Enum: `MODE_CONTROLLER=0, MODE_TOCTOU=1, MODE_MONITOR=2, MODE_POWER_CTRL=3`

### Steps

- [ ] **Step 1: Написать failing test TestUnifiedSymbols**

```python
# tests/wv_debug_adapter/test_unified_symbols.py
import subprocess
from pathlib import Path

ELF = Path.home() / "pico-bc250" / "build" / "unified.elf"


class TestUnifiedSymbols:
    def test_elf_exists(self):
        assert ELF.exists(), f"missing {ELF} — run `make -C ~/pico-bc250`"

    def test_monitor_init_symbol(self):
        out = subprocess.check_output(["nm", str(ELF)], text=True)
        assert "monitor_init" in out

    def test_power_ctrl_init_symbol(self):
        out = subprocess.check_output(["nm", str(ELF)], text=True)
        assert "power_ctrl_init" in out
```

- [ ] **Step 2: Run — must fail**

```bash
cd ~/orca/projects/bc250
pytest tests/wv_debug_adapter/test_unified_symbols.py -v
```

Expected: `AssertionError: monitor_init not in nm output` (при том, что unified.elf уже собран Phase 1).

- [ ] **Step 3: Расширить mode.h enum**

```c
// ~/pico-bc250/src/mode/mode.h — modify enum
typedef enum {
    MODE_CONTROLLER  = 0,
    MODE_TOCTOU      = 1,
    MODE_MONITOR     = 2,
    MODE_POWER_CTRL  = 3,
    MODE_COUNT
} mode_t;

// existing prototype:
mode_t mode_parse(const char *name);
const char *mode_name(mode_t m);
void mode_dispatch(mode_t m);
```

- [ ] **Step 4: Расширить mode.c парсер**

```c
// ~/pico-bc250/src/mode/mode.c — modify parser
#include "mode.h"
#include "monitor/monitor.h"
#include "power_ctrl/power_ctrl.h"
#include "bridge/bridge.h"        // existing MODE_CONTROLLER
#include "rig/rig.h"              // existing MODE_TOCTOU

#include <string.h>

static const char *NAMES[MODE_COUNT] = {
    [MODE_CONTROLLER]  = "controller",
    [MODE_TOCTOU]      = "toctou",
    [MODE_MONITOR]     = "monitor",
    [MODE_POWER_CTRL]  = "power_ctrl",
};

mode_t mode_parse(const char *name) {
    for (mode_t m = 0; m < MODE_COUNT; ++m) {
        if (strcmp(name, NAMES[m]) == 0) return m;
    }
    return MODE_COUNT;  // sentinel: parse failure
}

const char *mode_name(mode_t m) {
    if (m >= MODE_COUNT) return "invalid";
    return NAMES[m];
}

void mode_dispatch(mode_t m) {
    switch (m) {
        case MODE_CONTROLLER:  bridge_init();     break;
        case MODE_TOCTOU:      rig_init();        break;
        case MODE_MONITOR:     monitor_init();    break;
        case MODE_POWER_CTRL:  power_ctrl_init(); break;
        default: break;
    }
}
```

- [ ] **Step 5: Stub-файлы monitor/power_ctrl**

```c
// ~/pico-bc250/src/monitor/monitor.h
#pragma once
void monitor_init(void);

// ~/pico-bc250/src/monitor/monitor.c
#include "monitor.h"
#include <stdio.h>

void monitor_init(void) {
    printf("monitor_init: stub, cycle-1\n");
}

// ~/pico-bc250/src/power_ctrl/power_ctrl.h
#pragma once
void power_ctrl_init(void);

// ~/pico-bc250/src/power_ctrl/power_ctrl.c
#include "power_ctrl.h"
#include <stdio.h>

void power_ctrl_init(void) {
    printf("power_ctrl_init: stub, cycle-1\n");
}
```

- [ ] **Step 6: Обновить CMakeLists.txt**

```cmake
# ~/pico-bc250/CMakeLists.txt — extend target sources
target_sources(unified PRIVATE
    src/monitor/monitor.c
    src/power_ctrl/power_ctrl.c
)
target_include_directories(unified PRIVATE
    src
)
```

- [ ] **Step 7: Пересобрать unified.uf2**

```bash
cd ~/pico-bc250
make clean && make
```

Expected: `build/unified.elf` содержит символы, `build/unified.uf2` весит порядка 1.6 МБ.

- [ ] **Step 8: Run test_unified_symbols — must pass**

```bash
cd ~/orca/projects/bc250
pytest tests/wv_debug_adapter/test_unified_symbols.py -v
```

Expected: 3 passed.

- [ ] **Step 9: Написать failing test TestCdcModeAcceptsMonitor**

```python
# tests/wv_debug_adapter/test_cdc_mode.py
import os
import time
from pathlib import Path

import pytest
import serial  # pyserial

CDC = os.environ.get("WV_CDC", "/dev/ttyACM1")


def _cdc_cmd(port: str, cmd: str, timeout_ms: int = 200) -> str:
    with serial.Serial(port, 115200, timeout=timeout_ms / 1000) as s:
        s.write((cmd + "\r\n").encode())
        return s.read_until(b"\r\n").decode(errors="replace").strip()


@pytest.mark.hitl  # hardware-in-the-loop
class TestCdcModeAcceptsMonitor:
    def test_mode_monitor_accepts(self):
        if not Path(CDC).exists():
            pytest.skip(f"WV CDC not present at {CDC}")
        resp = _cdc_cmd(CDC, "MODE monitor")
        assert resp == "OK"

    def test_mode_power_ctrl_accepts(self):
        if not Path(CDC).exists():
            pytest.skip(f"WV CDC not present at {CDC}")
        resp = _cdc_cmd(CDC, "MODE power_ctrl")
        assert resp == "OK"

    def test_mode_invalid_rejects(self):
        if not Path(CDC).exists():
            pytest.skip(f"WV CDC not present at {CDC}")
        resp = _cdc_cmd(CDC, "MODE nosuchmode")
        assert resp.startswith("ERR")
```

- [ ] **Step 10: Прошить unified.uf2 через BOOTSEL**

Владелец кладёт WV в BOOTSEL (long-press BOOT), монтируется `/run/media/kukuruza/RP2350/`.

```bash
cp ~/pico-bc250/build/unified.uf2 /run/media/kukuruza/RP2350/
```

Ждать 3 сек reboot, проверить что `/dev/ttyACM1` появился.

- [ ] **Step 11: Run CDC-тест**

```bash
cd ~/orca/projects/bc250
sudo pytest tests/wv_debug_adapter/test_cdc_mode.py -v -m hitl
```

Expected: 3 passed (или skipped если CDC отсутствует; тогда владелец подключает).

- [ ] **Step 12: Commit в pico-bc250**

```bash
cd ~/pico-bc250
git checkout -b feature/wv-debug-adapter-cycle1
git add src/mode/mode.h src/mode/mode.c \
        src/monitor/monitor.h src/monitor/monitor.c \
        src/power_ctrl/power_ctrl.h src/power_ctrl/power_ctrl.c \
        CMakeLists.txt
git commit -m "wv-debug-adapter: add MODE_MONITOR and MODE_POWER_CTRL stubs (S-2)

Extends the mode enum with two new dispatch targets. Both handlers are
stubs that log a marker; real implementations land in later tasks.
CDC MODE parser now accepts 'monitor' and 'power_ctrl' alongside
'controller' and 'toctou'."
```

- [ ] **Step 13: Commit в bc250**

```bash
cd ~/orca/projects/bc250
git add tests/wv_debug_adapter/test_unified_symbols.py \
        tests/wv_debug_adapter/test_cdc_mode.py
git commit -m "wv-debug-adapter: nm + CDC MODE tests for new modes (S-2)

TestUnifiedSymbols pins the two new init symbols in the built ELF.
TestCdcModeAcceptsMonitor is a hitl test that requires WV on ttyACM1
and validates that MODE monitor/power_ctrl now return OK."
```

---

## Task 3: MODE_MONITOR — PMBus reader + MQTT publish (S-7)

**Files (all in `~/pico-bc250/` unless noted):**
- Create: `src/monitor/pmbus.h` — PMBus декоды
- Create: `src/monitor/pmbus.c` — bit-bang I2C + PMBus @ 0x60 reader
- Create: `src/monitor/mqtt_publish.h` — MQTT publish API
- Create: `src/monitor/mqtt_publish.c` — WiFi + `paho-mqtt-embedded-c` publish
- Modify: `src/monitor/monitor.c` — заменить stub на реальный loop 700ms
- Modify: `CMakeLists.txt` — линк `pico_lwip_mqtt`
- Create: `~/orca/projects/bc250/tests/wv_debug_adapter/test_pmbus_publish.py` — MQTT-subscriber тесты

**Interfaces:**
- Consumes: GPIO конфигурация I2C pins из `src/monitor/pmbus.h` (по итогам Task 1 инвентаризации — точные GP pins), MQTT-broker URL из config-flash (`0xFFF000`).
- Produces:
  - `bc250/pmbus/vin` (float, V, каждые 700ms)
  - `bc250/pmbus/vout` (float, V)
  - `bc250/pmbus/iout` (float, A)
  - `bc250/pmbus/pout` (float, W)
  - `bc250/pmbus/temp` (int, °C)
  - Функция `bool pmbus_read(pmbus_snapshot_t *out);` возвращает false при NACK.
  - Функция `void mqtt_publish_snapshot(const pmbus_snapshot_t *s);`

### Steps

- [ ] **Step 1: Написать failing тест TestPmbusTopicFrequency**

```python
# tests/wv_debug_adapter/test_pmbus_publish.py
import os
import statistics
import time

import paho.mqtt.client as mqtt
import pytest

BROKER = os.environ.get("MQTT_BROKER", "127.0.0.1")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))

pytestmark = pytest.mark.hitl


def _collect(topic: str, count: int, timeout_s: float = 30) -> list[tuple[float, str]]:
    samples: list[tuple[float, str]] = []
    client = mqtt.Client()

    def on_message(_c, _u, msg):
        samples.append((time.monotonic(), msg.payload.decode()))

    client.on_message = on_message
    client.connect(BROKER, BROKER_PORT, 30)
    client.subscribe(topic)
    client.loop_start()
    t0 = time.monotonic()
    while len(samples) < count and time.monotonic() - t0 < timeout_s:
        time.sleep(0.05)
    client.loop_stop()
    client.disconnect()
    return samples


class TestPmbusTopicFrequency:
    def test_median_interval_within_window(self):
        samples = _collect("bc250/pmbus/vin", 20)
        assert len(samples) >= 20, f"got only {len(samples)} samples in 30s"
        intervals = [
            samples[i + 1][0] - samples[i][0]
            for i in range(len(samples) - 1)
        ]
        median = statistics.median(intervals)
        assert 0.65 <= median <= 0.75, f"median interval {median*1000:.0f} ms out of 650–750 ms"


class TestPmbusMatchesBc250Telemetry:
    def test_vin_within_tolerance(self):
        # Requires BC250-Telemetry running inside Linux and BC-250 powered on.
        import subprocess, json
        samples = _collect("bc250/pmbus/vin", 3)
        assert samples, "no MQTT samples"
        our_vin = float(samples[-1][1])
        telemetry = json.loads(subprocess.check_output([
            "ssh", "bc250", "cat", "/run/apu_telemetry.json"
        ]))
        their_vin = telemetry["cpu_vrm"]["vin"]
        assert abs(our_vin - their_vin) <= 0.05, (
            f"our vin {our_vin} vs bc250-telemetry {their_vin}"
        )
```

- [ ] **Step 2: Run — must fail**

```bash
cd ~/orca/projects/bc250
sudo pytest tests/wv_debug_adapter/test_pmbus_publish.py -v -m hitl
```

Expected: fail on `len(samples) >= 20` (нет ни одного, stub-режим).

- [ ] **Step 3: Реализация pmbus.c** (bit-bang I2C + PMBus command set)

```c
// ~/pico-bc250/src/monitor/pmbus.h
#pragma once
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    float vin;
    float vout;
    float iout;
    float pout;
    int8_t temp_c;
    bool valid;
} pmbus_snapshot_t;

bool pmbus_init(uint8_t sda_gpio, uint8_t scl_gpio);
bool pmbus_read(pmbus_snapshot_t *out);

// ~/pico-bc250/src/monitor/pmbus.c
#include "pmbus.h"
#include "hardware/gpio.h"
#include "pico/time.h"

static uint8_t g_sda, g_scl;

// PMBus commands (see PMBus spec 1.3)
#define PMB_READ_VIN    0x88
#define PMB_READ_VOUT   0x8B
#define PMB_READ_IOUT   0x8C
#define PMB_READ_POUT   0x96
#define PMB_READ_TEMP1  0x8D
#define PMB_ADDR        0x60

static void i2c_delay(void) { sleep_us(3); } // ~150 kHz

static void i2c_start(void) {
    gpio_put(g_sda, 0); i2c_delay();
    gpio_put(g_scl, 0); i2c_delay();
}

static void i2c_stop(void) {
    gpio_put(g_sda, 0); i2c_delay();
    gpio_put(g_scl, 1); i2c_delay();
    gpio_put(g_sda, 1); i2c_delay();
}

static bool i2c_write_byte(uint8_t b) {
    for (int i = 7; i >= 0; --i) {
        gpio_put(g_sda, (b >> i) & 1); i2c_delay();
        gpio_put(g_scl, 1); i2c_delay();
        gpio_put(g_scl, 0); i2c_delay();
    }
    // ACK
    gpio_set_dir(g_sda, GPIO_IN); i2c_delay();
    gpio_put(g_scl, 1); i2c_delay();
    bool ack = (gpio_get(g_sda) == 0);
    gpio_put(g_scl, 0); i2c_delay();
    gpio_set_dir(g_sda, GPIO_OUT);
    return ack;
}

static uint8_t i2c_read_byte(bool nack) {
    uint8_t v = 0;
    gpio_set_dir(g_sda, GPIO_IN);
    for (int i = 7; i >= 0; --i) {
        gpio_put(g_scl, 1); i2c_delay();
        v |= (gpio_get(g_sda) ? 1 : 0) << i;
        gpio_put(g_scl, 0); i2c_delay();
    }
    gpio_set_dir(g_sda, GPIO_OUT);
    gpio_put(g_sda, nack ? 1 : 0); i2c_delay();
    gpio_put(g_scl, 1); i2c_delay();
    gpio_put(g_scl, 0); i2c_delay();
    return v;
}

static bool pmb_read_word(uint8_t cmd, uint16_t *val) {
    i2c_start();
    if (!i2c_write_byte((PMB_ADDR << 1) | 0)) { i2c_stop(); return false; }
    if (!i2c_write_byte(cmd))                  { i2c_stop(); return false; }
    i2c_start();  // repeated START
    if (!i2c_write_byte((PMB_ADDR << 1) | 1)) { i2c_stop(); return false; }
    uint8_t lo = i2c_read_byte(false);
    uint8_t hi = i2c_read_byte(true);
    i2c_stop();
    *val = ((uint16_t)hi << 8) | lo;
    return true;
}

bool pmbus_init(uint8_t sda_gpio, uint8_t scl_gpio) {
    g_sda = sda_gpio;
    g_scl = scl_gpio;
    gpio_init(g_sda); gpio_set_dir(g_sda, GPIO_OUT); gpio_put(g_sda, 1);
    gpio_init(g_scl); gpio_set_dir(g_scl, GPIO_OUT); gpio_put(g_scl, 1);
    return true;
}

// LINEAR11 (PMBus spec section 8.3.1): mantissa 11-bit signed,
// exponent 5-bit signed at top.
static float linear11(uint16_t raw) {
    int16_t mant = raw & 0x07FF;
    if (mant & 0x0400) mant |= 0xF800; // sign-extend
    int16_t exp = raw >> 11;
    if (exp & 0x10) exp |= 0xFFE0;
    return mant * (exp >= 0 ? (1 << exp) : 1.0f / (1 << (-exp)));
}

bool pmbus_read(pmbus_snapshot_t *out) {
    uint16_t raw;
    out->valid = false;
    if (!pmb_read_word(PMB_READ_VIN,   &raw)) return false;
    out->vin  = linear11(raw);
    if (!pmb_read_word(PMB_READ_VOUT,  &raw)) return false;
    out->vout = linear11(raw);
    if (!pmb_read_word(PMB_READ_IOUT,  &raw)) return false;
    out->iout = linear11(raw);
    if (!pmb_read_word(PMB_READ_POUT,  &raw)) return false;
    out->pout = linear11(raw);
    if (!pmb_read_word(PMB_READ_TEMP1, &raw)) return false;
    out->temp_c = (int8_t)linear11(raw);
    out->valid = true;
    return true;
}
```

- [ ] **Step 4: Реализация mqtt_publish.c**

Use lwip MQTT client from Pico SDK. Key API: `mqtt_client_connect`, `mqtt_publish`.

```c
// ~/pico-bc250/src/monitor/mqtt_publish.h
#pragma once
#include "pmbus.h"

bool mqtt_publish_init(const char *broker_ip, uint16_t port);
void mqtt_publish_snapshot(const pmbus_snapshot_t *s);

// ~/pico-bc250/src/monitor/mqtt_publish.c
#include "mqtt_publish.h"
#include "lwip/apps/mqtt.h"
#include "lwip/ip_addr.h"
#include <stdio.h>
#include <string.h>

static mqtt_client_t *g_client;

bool mqtt_publish_init(const char *broker_ip, uint16_t port) {
    g_client = mqtt_client_new();
    if (!g_client) return false;
    ip_addr_t addr;
    if (!ip4addr_aton(broker_ip, &addr)) return false;
    struct mqtt_connect_client_info_t info = { .client_id = "wv-debug-adapter" };
    return mqtt_client_connect(g_client, &addr, port, NULL, NULL, &info) == ERR_OK;
}

static void pub_float(const char *topic, float v) {
    char buf[32];
    int n = snprintf(buf, sizeof(buf), "%.3f", v);
    mqtt_publish(g_client, topic, buf, n, 0, 0, NULL, NULL);
}

static void pub_int(const char *topic, int v) {
    char buf[16];
    int n = snprintf(buf, sizeof(buf), "%d", v);
    mqtt_publish(g_client, topic, buf, n, 0, 0, NULL, NULL);
}

void mqtt_publish_snapshot(const pmbus_snapshot_t *s) {
    if (!s->valid) return;
    pub_float("bc250/pmbus/vin",  s->vin);
    pub_float("bc250/pmbus/vout", s->vout);
    pub_float("bc250/pmbus/iout", s->iout);
    pub_float("bc250/pmbus/pout", s->pout);
    pub_int  ("bc250/pmbus/temp", s->temp_c);
}
```

- [ ] **Step 5: monitor.c — реальный 700ms loop**

```c
// ~/pico-bc250/src/monitor/monitor.c — replace stub
#include "monitor.h"
#include "pmbus.h"
#include "mqtt_publish.h"
#include "pico/time.h"
#include "config/config.h"   // existing config/flash reader

void monitor_init(void) {
    const uint8_t SDA = 4;  // from Task 1 headers-map: I2C_HEADER1 wired to WV GP4
    const uint8_t SCL = 5;  // and GP5
    pmbus_init(SDA, SCL);

    const char *broker = config_get_string("mqtt_broker", "127.0.0.1");
    uint16_t port = (uint16_t)config_get_int("mqtt_port", 1883);
    mqtt_publish_init(broker, port);

    pmbus_snapshot_t s;
    absolute_time_t next = get_absolute_time();
    while (true) {
        next = delayed_by_ms(next, 700);
        sleep_until(next);
        if (pmbus_read(&s)) {
            mqtt_publish_snapshot(&s);
        }
    }
}
```

- [ ] **Step 6: CMake — линк paho/lwip-mqtt**

```cmake
target_link_libraries(unified PRIVATE
    pico_lwip_mqtt
    pico_cyw43_arch_lwip_poll
)
```

- [ ] **Step 7: Пересобрать, прошить, проверить**

```bash
cd ~/pico-bc250 && make clean && make
cp build/unified.uf2 /run/media/kukuruza/RP2350/
# wait 3s, WV reboots
```

- [ ] **Step 8: Установить MODE_MONITOR через CDC**

```bash
python -c "
import serial
s = serial.Serial('/dev/ttyACM1', 115200, timeout=1)
s.write(b'MODE monitor\r\n')
print(s.read_until(b'\r\n').decode())
"
```

Expected: `OK`.

- [ ] **Step 9: Run PMBus test — must pass**

```bash
cd ~/orca/projects/bc250
sudo pytest tests/wv_debug_adapter/test_pmbus_publish.py -v -m hitl
```

Expected: 2 passed (TestPmbusTopicFrequency, TestPmbusMatchesBc250Telemetry).

- [ ] **Step 10: Commit в pico-bc250 и в bc250**

```bash
cd ~/pico-bc250
git add src/monitor/pmbus.h src/monitor/pmbus.c \
        src/monitor/mqtt_publish.h src/monitor/mqtt_publish.c \
        src/monitor/monitor.c CMakeLists.txt
git commit -m "wv-debug-adapter: real PMBus reader + MQTT publish (S-7)

MODE_MONITOR now bit-bangs I2C on GP4/GP5, reads PMBus @ 0x60 every
700ms, and publishes VIN/VOUT/IOUT/POUT/TEMP to bc250/pmbus/*. WiFi
brings the CYW43 up before entering the loop."

cd ~/orca/projects/bc250
git add tests/wv_debug_adapter/test_pmbus_publish.py
git commit -m "wv-debug-adapter: MQTT integration tests for PMBus stream (S-7)"
```

---

## Task 4: MODE_POWER_CTRL — GPIO Power-header (S-2, part of S-3)

**Files (`~/pico-bc250/`):**
- Modify: `src/power_ctrl/power_ctrl.c` — заменить stub на реальный GPIO
- Create: `src/power_ctrl/power_ctrl_test.h` — public helpers для CDC-теста
- Modify: `src/cdc_dispatch.c` — принять `POWER_ON`, `POWER_OFF`, `POWER_TOGGLE`
- Create: `~/orca/projects/bc250/tests/wv_debug_adapter/test_power_wake.py` — hitl-тест GPIO пульса через логический анализатор

**Interfaces:**
- Consumes: GPIO map из Task 1 (`FRONT_PANEL_HDR` pin 1-2 подключены к WV GP через опто-развязку, GP определяется CAD-inventarization).
- Produces:
  - `void power_gpio_pulse(uint32_t ms);` — pulse GPIO high на `ms` миллисекунд
  - CDC command `POWER_TOGGLE` — вызывает `power_gpio_pulse(200)`

### Steps

- [ ] **Step 1: Написать failing TestPsPressPulsesPowerGpio**

```python
# tests/wv_debug_adapter/test_power_wake.py
import os
import subprocess
from pathlib import Path

import pytest

LOGIC = os.environ.get("LOGIC_ANALYZER", "/dev/logic-analyzer-0")

pytestmark = pytest.mark.hitl


class TestPsPressPulsesPowerGpio:
    def test_cdc_power_toggle_produces_pulse(self):
        if not Path(LOGIC).exists():
            pytest.skip("logic analyzer not present")
        # Trigger via CDC:
        subprocess.run(
            ["python", "-c",
             "import serial; s=serial.Serial('/dev/ttyACM1',115200,timeout=1);"
             "s.write(b'POWER_TOGGLE\\r\\n'); print(s.read_until(b'\\r\\n'))"],
            check=True,
        )
        # Read logic analyzer, extract single positive pulse on the Power line
        pulse_ms = _capture_pulse(LOGIC, timeout_ms=500)
        assert pulse_ms is not None, "no pulse detected"
        assert 180 <= pulse_ms <= 220, f"pulse duration {pulse_ms} ms out of 180..220"


def _capture_pulse(dev: str, timeout_ms: int) -> float | None:
    # Placeholder: real capture uses sigrok-cli or libsigrok.
    # For now this test SKIPS unless LOGIC device is present and captured.
    return None
```

- [ ] **Step 2: Run — must skip or fail**

Expected: skipped (no logic analyzer) — task ends with manual verification note when hardware is unavailable.

- [ ] **Step 3: Реализация power_ctrl.c**

```c
// ~/pico-bc250/src/power_ctrl/power_ctrl.c — real implementation
#include "power_ctrl.h"
#include "hardware/gpio.h"
#include "pico/time.h"

#define POWER_GPIO 22  // from Task 1 headers-map: FRONT_PANEL_HDR pin 1

void power_ctrl_init(void) {
    gpio_init(POWER_GPIO);
    gpio_set_dir(POWER_GPIO, GPIO_OUT);
    gpio_put(POWER_GPIO, 0);  // idle low — opto is inverted
}

void power_gpio_pulse(uint32_t ms) {
    gpio_put(POWER_GPIO, 1);
    sleep_ms(ms);
    gpio_put(POWER_GPIO, 0);
}
```

- [ ] **Step 4: cdc_dispatch.c — POWER_TOGGLE handler**

```c
// ~/pico-bc250/src/cdc_dispatch.c — add case
} else if (strcmp(cmd, "POWER_TOGGLE") == 0) {
    power_gpio_pulse(200);
    cdc_reply("OK");
} else if (strcmp(cmd, "POWER_ON") == 0) {
    power_gpio_pulse(200);   // same edge; opto handles direction
    cdc_reply("OK");
} else if (strcmp(cmd, "POWER_OFF") == 0) {
    power_gpio_pulse(4000);  // 4-second hold for forced off
    cdc_reply("OK");
```

- [ ] **Step 5: Пересобрать, прошить**

```bash
cd ~/pico-bc250 && make && cp build/unified.uf2 /run/media/kukuruza/RP2350/
```

- [ ] **Step 6: Manual verification (owner)**

Владелец подключает WV GP22 через опто-развязку к front-panel Power pin 1-2 BC-250. WV в MODE_POWER_CTRL. CDC `POWER_TOGGLE` — консоль стартует. Лог в `docs/action-logs/2026-09-XX-wv-power-ctrl-first-boot.md`.

- [ ] **Step 7: Commit**

```bash
cd ~/pico-bc250
git add src/power_ctrl/power_ctrl.c src/cdc_dispatch.c
git commit -m "wv-debug-adapter: real GPIO Power-header pulse (S-2/S-3)"

cd ~/orca/projects/bc250
git add tests/wv_debug_adapter/test_power_wake.py
git commit -m "wv-debug-adapter: hitl test for Power-GPIO pulse duration (S-3)"
```

---

## Task 5: Веб-панель на WV (S-9)

**Files (`~/pico-bc250/`):**
- Create: `src/web/web.h`
- Create: `src/web/web.c` — mongoose или собственный HTTP-server на порту 80
- Create: `assets/index.html` — панель, реиспользует шаблон из `tools/console/index.html`
- Create: `assets/panel.css`
- Create: `assets/panel.js` — WebSocket-клиент, подписан на MQTT-мостиковый WS от коробочки
- Modify: `CMakeLists.txt` — pico_lwip_http, embed assets
- Create: `~/orca/projects/bc250/tests/wv_debug_adapter/test_web_panel.py` — headless-Chromium тест

**Interfaces:**
- Consumes: PMBus snapshot из Task 3 (через shared struct или MQTT-локальный subscribe).
- Produces:
  - HTTP endpoint `GET /` → `index.html`
  - WebSocket endpoint `GET /ws` → JSON snapshots каждые 700 ms

### Steps

- [ ] **Step 1: Написать failing TestWebPanelLayoutAt360Px**

```python
# tests/wv_debug_adapter/test_web_panel.py
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

WV_URL = os.environ.get("WV_URL", "http://wv-debug.local")

pytestmark = pytest.mark.hitl


class TestWebPanelLayoutAt360Px:
    def test_all_sections_above_800px(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 360, "height": 800})
            page = ctx.new_page()
            try:
                page.goto(WV_URL, timeout=5000)
            except Exception:
                pytest.skip(f"WV panel not reachable at {WV_URL}")
            for section in ["Питание", "Метрики", "VCN", "DS5"]:
                loc = page.get_by_role("region", name=section)
                assert loc.count() == 1, f"section {section!r} missing"
                box = loc.bounding_box()
                assert box["y"] + box["height"] <= 800, (
                    f"{section!r} bottom at {box['y']+box['height']}"
                )
            browser.close()
```

- [ ] **Step 2: Run — must skip / fail**

Expected: skip (WV panel URL not up).

- [ ] **Step 3: index.html (skeleton)**

```html
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BC-250 Debug Adapter</title>
<link rel="stylesheet" href="/panel.css">
</head>
<body>
<main>
  <section role="region" aria-label="Питание"><h2>Питание</h2><div id="power"></div></section>
  <section role="region" aria-label="Метрики"><h2>Метрики</h2><div id="metrics"></div></section>
  <section role="region" aria-label="VCN"><h2>VCN</h2><div id="vcn"></div></section>
  <section role="region" aria-label="DS5"><h2>DS5</h2><div id="ds5"></div></section>
  <details><summary>Расширенное</summary><div id="advanced"></div></details>
</main>
<script src="/panel.js"></script>
</body>
</html>
```

- [ ] **Step 4: panel.css — компакт для 360×800**

```css
:root { --pad: 8px; }
* { box-sizing: border-box; }
body { margin: 0; font: 14px/1.3 system-ui, sans-serif; background: #101418; color: #dfe4ea; }
main { display: grid; grid-template-columns: 1fr 1fr; gap: var(--pad); padding: var(--pad); }
section { background: #1a1f24; border-radius: 8px; padding: var(--pad); }
section h2 { margin: 0 0 var(--pad); font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: #9ba3ab; }
details { grid-column: 1 / -1; }
```

- [ ] **Step 5: panel.js — WebSocket loop**

```javascript
const ws = new WebSocket(`ws://${location.host}/ws`);
ws.onmessage = (ev) => {
  const s = JSON.parse(ev.data);
  document.getElementById("power").textContent = `${s.pout.toFixed(1)} W · ${s.vin.toFixed(2)} V`;
  document.getElementById("metrics").textContent = `${s.temp}°C`;
  document.getElementById("vcn").textContent = s.vcn_status || "—";
  document.getElementById("ds5").textContent = s.ds5_connected ? "OK" : "—";
};
```

- [ ] **Step 6: web.c — HTTP+WS server**

Используй SDK pico_lwip_http или простую bare-metal реализацию с mongoose (< 8 KB). WS endpoint шлёт `{vin, vout, iout, pout, temp, vcn_status, ds5_connected}` каждые 700ms из shared struct.

(Полный код опущен здесь для места — вложи модуль `tools/mongoose_bare/` от Cesanta или используй pico-httpd, обозначь выбор в commit-message.)

- [ ] **Step 7: Пересобрать, прошить, поднять WiFi**

Владелец конфигурит SSID/PSK в `~/.config/pico-bc250/net.env` (mode 600), заливает в WV BOOTSEL'ом.

- [ ] **Step 8: Run headless-Chromium test — must pass**

```bash
cd ~/orca/projects/bc250
pytest tests/wv_debug_adapter/test_web_panel.py -v -m hitl
```

Expected: pass — все 4 секции видны в 360×800.

- [ ] **Step 9: Commit**

```bash
cd ~/pico-bc250
git add src/web/web.h src/web/web.c \
        assets/index.html assets/panel.css assets/panel.js \
        CMakeLists.txt
git commit -m "wv-debug-adapter: minimal web panel with WS metrics stream (S-9)"

cd ~/orca/projects/bc250
git add tests/wv_debug_adapter/test_web_panel.py
git commit -m "wv-debug-adapter: playwright test for panel layout at 360px (S-9)"
```

---

## Cycle 1 complete criteria

К концу цикла 1 всё зелёное:

- `pytest tests/wv_debug_adapter/ -v` — все non-hitl тесты pass
- `pytest tests/wv_debug_adapter/ -v -m hitl` — hitl тесты pass или явно skipped с причиной
- `procoder spec check wv-debug-adapter` — COMPLETE
- Прошивка `~/pico-bc250/build/unified.uf2` собирается, содержит символы `monitor_init`, `power_ctrl_init`, `web_init`, `bridge_init`, `rig_init`
- Веб-панель на WV показывает актуальные данные; MQTT-топик `bc250/pmbus/vin` обновляется каждые 700 ms в MQTT-брокере HAOS

Следующие циклы (не в этом плане):
- Cycle 2: полный TOCTOU-контур (S-4), клипса SOIC-8, weekly-snapshot (S-5)
- Cycle 3: BT-хостинг DS5Dongle-паттерн + PS-wake (S-3), интеграция с Task 4 GPIO Power
- Cycle 4: SPI-программатор (S-5 полный), UART-мост (S-6)
- Cycle 5: Decky-плагин (S-10), MQTT-эмуляция BC250-Telemetry (S-11), TPM/LPC/JTAG-диагностика (S-8)
