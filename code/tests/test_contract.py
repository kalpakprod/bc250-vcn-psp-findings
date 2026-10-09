"""Общий гейт контракта. Одинаковый во всех репозиториях, раскатывается
из harness скриптом tools/contour_sync.py. Stdlib, без зависимостей.

Запуск:  make test   или   python3 tests/test_contract.py
"""

import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "AGENTS.md"
LIMIT = 31_000  # Codex режет AGENTS.md на 32 КиБ, держим запас.
MAX_SKILL_CHARS = 24_000  # грубая прокси L2 (<5k токенов)
CONTRACT_LIMIT = 13_000  # не больше прежнего контракта; качество важнее краткости
SECTIONS = [
    "role",
    "limits",
    "autonomy",
    "scope_ladder",
    "work",
    "reporting",
    "shortcuts",
    "keywords",
]
TRANSLATION = ROOT / "docs/contract-ru.md"
# Строгие правила для скиллов и инструкций там, где проект их принял (есть .strict).
STRICT = (ROOT / ".agents/skills/.strict").is_file()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict:
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    out, lines, i = {}, m.group(1).splitlines(), 0
    while i < len(lines):
        if re.match(r"^[A-Za-z0-9_-]+:", lines[i]):
            k, _, v = lines[i].partition(":")
            v = v.strip()
            if v in (">", ">-", "|", "|-", ""):
                j, folded = i + 1, []
                while j < len(lines) and re.match(r"^( +|\t)", lines[j]):
                    folded.append(lines[j].strip())
                    j += 1
                v = " ".join(folded)
            out[k.strip()] = v.strip("'\"")
        i += 1
    return out


def contract_block(text: str) -> str:
    m = re.search(r"<contract>.*</contract>", text, re.DOTALL)
    return m.group(0) if m else ""


class TestContract(unittest.TestCase):
    def test_no_cyrillic_in_model_text(self):
        files = sorted((ROOT / ".claude/commands").glob("*.md"))
        if STRICT:
            files += sorted((ROOT / "instructions").glob("*.md"))
        for f in files:
            body = re.sub(r"\A---\n.*?\n---\n", "", read(f), flags=re.DOTALL)
            body = re.sub(r"<examples_ru>.*?</examples_ru>", "", body, flags=re.DOTALL)
            body = body.replace("«Понял задачу так: …»", "")
            self.assertIsNone(
                re.search("[А-Яа-яЁё]", body),
                f"{f.relative_to(ROOT)}: кириллица в тексте для модели",
            )

    def test_contract_budget(self):
        size = len(contract_block(read(AGENTS)).encode())
        self.assertGreater(size, 0, "нет блока <contract>")
        self.assertLessEqual(size, CONTRACT_LIMIT, f"контракт {size} байт")

    def test_contract_sections(self):
        block = contract_block(read(AGENTS))
        for name in SECTIONS:
            self.assertIn(f"<{name}>", block, f"в контракте нет раздела <{name}>")

    def test_sts_directive_rule(self):
        self.assertIn("$stop-that-shit", contract_block(read(AGENTS)))

    def test_translation_fresh(self):
        import hashlib

        self.assertTrue(TRANSLATION.is_file(), "нет docs/contract-ru.md")
        want = hashlib.sha256(contract_block(read(AGENTS)).encode()).hexdigest()
        first = read(TRANSLATION).splitlines()[0]
        self.assertEqual(
            first,
            f"<!-- source-sha256: {want} -->",
            "контракт изменён, а перевод docs/contract-ru.md нет: обнови перевод и хеш",
        )

    def test_single_rules_file(self):
        self.assertTrue(AGENTS.is_file(), "нет AGENTS.md")
        self.assertFalse(
            (ROOT / "CLAUDE.md").exists(),
            "CLAUDE.md не нужен: Claude Code читает AGENTS.md",
        )

    def test_agents_fits_limit(self):
        size = len(AGENTS.read_bytes())
        self.assertLessEqual(size, LIMIT, f"AGENTS.md {size} байт, лимит {LIMIT}")

    def test_project_block_and_map(self):
        text = read(AGENTS)
        self.assertRegex(
            text,
            r"\A(# [^\n]*\n\s*)?<project>",
            "AGENTS.md должен начинаться с блока <project>",
        )
        block = re.search(r"<project>.*?```text\n(.*?)```", text, re.DOTALL)
        self.assertIsNotNone(block, "в <project> нет карты ```text")
        for line in block.group(1).splitlines():
            if not line.strip() or line.startswith(" "):
                continue
            path = line.split()[0]
            self.assertTrue((ROOT / path).exists(), f"карта: {path} нет на диске")

    def test_xml_tags_balanced(self):
        files = [AGENTS] + sorted((ROOT / ".claude/commands").glob("*.md"))
        tag = re.compile(r"^<(/?)([a-z_]+)>", re.M)
        for f in files:
            body = re.sub(r"```.*?```", "", read(f), flags=re.DOTALL)
            body = re.sub(r"^<([a-z_]+)>.*</\1>$", "", body, flags=re.M)
            stack = []
            for closing, name in tag.findall(body):
                if closing:
                    self.assertTrue(
                        stack and stack[-1] == name,
                        f"{f.relative_to(ROOT)}: лишний </{name}>",
                    )
                    stack.pop()
                else:
                    stack.append(name)
            self.assertEqual(stack, [], f"{f.relative_to(ROOT)}: не закрыты {stack}")

    def test_hooks_wired(self):
        settings = json.loads(read(ROOT / ".claude/settings.json"))
        self.assertIn("UserPromptSubmit", settings.get("hooks", {}))
        self.assertIn("PostToolUse", settings.get("hooks", {}))
        self.assertIn("PreToolUse", settings.get("hooks", {}))
        self.assertIn("Stop", settings.get("hooks", {}))
        wiring = read(ROOT / ".claude/settings.json") + read(ROOT / ".codex/hooks.json")
        self.assertNotIn("drift-check", wiring, "drift-check убран")
        self.assertNotIn("goal-anchor", wiring, "goal-anchor убран")
        for h in [
            "task-capture.sh",
            "task-intake.py",
            "keep-going.py",
            "keep-going.sh",
            "action-log.sh",
            "web-guard.sh",
            "git-guard.sh",
        ]:
            p = ROOT / ".claude/hooks" / h
            self.assertTrue(
                p.is_file() and os.access(p, os.X_OK),
                f"хук {h} отсутствует или не исполняемый",
            )

    def test_skills_valid(self):
        root = ROOT / ".agents/skills"
        if not root.is_dir():
            return
        self.assertTrue(
            (ROOT / ".claude/skills").exists(),
            "нет ссылки .claude/skills: Claude Code не увидит скиллы",
        )
        # Чужие скиллы (апстрим, плагины) в .agents/skills/.vendored, по имени
        # в строке: их не режем под наш лимит, иначе теряются обновления авторов.
        vf = root / ".vendored"
        vendored = set(read(vf).split()) if vf.is_file() else set()
        for sf in sorted(root.glob("*/SKILL.md")):
            fm, text = frontmatter(read(sf)), read(sf)
            self.assertIn("name", fm, f"{sf}: нет name")
            self.assertGreaterEqual(
                len(fm.get("description", "")),
                20,
                f"{sf}: description короче 20 символов",
            )
            if sf.parent.name != "_template":
                self.assertEqual(fm["name"], sf.parent.name, f"{sf}: name != каталог")
            if sf.parent.name not in vendored:
                self.assertLessEqual(
                    len(text), MAX_SKILL_CHARS, f"{sf}: тело больше L2"
                )
                desc = fm.get("description", "")
                if not STRICT:
                    continue
                if sf.parent.name != "_template":
                    self.assertIn("Use ", desc, f"{sf}: в description нет «Use when»")
                self.assertIn(
                    "Do not use", desc, f"{sf}: в description нет «Do not use»"
                )

    def test_relative_links_resolve(self):
        files = [ROOT / f for f in ["AGENTS.md", "README.md", "MISTAKES.md"]]
        files += sorted((ROOT / ".claude/commands").glob("*.md"))
        link = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
        for f in [f for f in files if f.is_file()]:
            for target in link.findall(read(f)):
                if re.match(r"^[a-z]+:", target) or target.startswith("<"):
                    continue
                self.assertTrue(
                    (f.parent / target).exists(),
                    f"{f.relative_to(ROOT)}: битая ссылка {target}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
