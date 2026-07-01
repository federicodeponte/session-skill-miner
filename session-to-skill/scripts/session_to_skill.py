#!/usr/bin/env python3
"""Extract reusable-skill signals from agent session logs.

The script is intentionally conservative. It does not decide final skill
quality; it produces repeatable scaffolding for an agent to review.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {".md", ".txt", ".jsonl", ".json"}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-./=]{8,})"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
]
COMMAND_RE = re.compile(r"`([^`\n]{3,120})`|\b((?:npm|pnpm|yarn|python3?|pytest|uv|git|rg|jq|npx|bash|node)\s+[^\n]{2,120})")
PHRASE_RE = re.compile(r"\b(?:always|never|remember|next time|from now on|again|repeated|same workflow|turn .* into a skill|make .* skill)\b", re.I)
CORRECTION_RE = re.compile(r"\b(?:wrong|mistake|not that|don't|do not|never|you missed|instead|stop|fix)\b", re.I)
WORKFLOW_RE = re.compile(r"\b(?:build|create|draft|review|audit|validate|verify|deploy|extract|summarize|convert|publish|generate|test)\b", re.I)


@dataclass(frozen=True)
class Event:
    source: Path
    line: int
    role: str
    text: str


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path
        return
    for child in sorted(path.rglob("*")):
        if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS:
            yield child


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: f"{m.group(1) if m.groups() else 'secret'}=[REDACTED]", redacted)
    redacted = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", redacted)
    return redacted


def extract_jsonl_events(path: Path) -> Iterable[Event]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                yield Event(path, line_no, "text", redact(raw))
                continue
            role = str(obj.get("role") or obj.get("type") or obj.get("message", {}).get("role") or "unknown")
            text_parts: list[str] = []
            message = obj.get("message") if isinstance(obj.get("message"), dict) else obj
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        value = item.get("text") or item.get("content") or item.get("name")
                        if isinstance(value, str):
                            text_parts.append(value)
                    elif isinstance(item, str):
                        text_parts.append(item)
            text = " ".join(part.strip() for part in text_parts if part.strip())
            if text:
                yield Event(path, line_no, role, redact(text))


def extract_text_events(path: Path) -> Iterable[Event]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, 1):
            text = raw.strip()
            if text:
                yield Event(path, line_no, "text", redact(text))


def extract_events(paths: list[Path]) -> list[Event]:
    events: list[Event] = []
    for root in paths:
        for file_path in iter_files(root):
            if file_path.suffix.lower() == ".jsonl":
                events.extend(extract_jsonl_events(file_path))
            else:
                events.extend(extract_text_events(file_path))
    return events


def normalize_phrase(text: str) -> str:
    text = re.sub(r"https?://\S+", "[URL]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120]


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:48] or "session-derived-skill"


def score_events(events: list[Event]) -> dict[str, object]:
    command_counts: Counter[str] = Counter()
    phrase_hits: list[Event] = []
    correction_hits: list[Event] = []
    workflow_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    by_source: defaultdict[str, int] = defaultdict(int)

    for event in events:
        source_counts[str(event.source)] += 1
        by_source[str(event.source)] += 1
        text = event.text
        if PHRASE_RE.search(text):
            phrase_hits.append(event)
        if CORRECTION_RE.search(text):
            correction_hits.append(event)
        for match in COMMAND_RE.finditer(text):
            command = match.group(1) or match.group(2)
            if command:
                command_counts[normalize_phrase(command)] += 1
        if WORKFLOW_RE.search(text):
            words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower())
            for word in words:
                if WORKFLOW_RE.fullmatch(word):
                    workflow_counts[word] += 1

    return {
        "commands": command_counts,
        "phrases": phrase_hits,
        "corrections": correction_hits,
        "workflows": workflow_counts,
        "sources": source_counts,
        "by_source": by_source,
    }


def cite(event: Event) -> str:
    return f"{event.source.name}:{event.line}"


def proposal_rows(events: list[Event], scores: dict[str, object]) -> list[tuple[str, str, str]]:
    workflows: Counter[str] = scores["workflows"]  # type: ignore[assignment]
    commands: Counter[str] = scores["commands"]  # type: ignore[assignment]
    corrections: list[Event] = scores["corrections"]  # type: ignore[assignment]
    rows: list[tuple[str, str, str]] = []

    for verb, count in workflows.most_common(6):
        if count >= 2:
            rows.append((f"{verb}-workflow", str(count), f"Repeated `{verb}` workflow language"))

    for command, count in commands.most_common(5):
        if count >= 2:
            rows.append((slugify(command.split()[0] + "-workflow"), str(count), f"Repeated command: `{command}`"))

    if len(corrections) >= 2:
        evidence = ", ".join(cite(event) for event in corrections[:3])
        rows.append(("correction-patterns", str(len(corrections)), f"Repeated correction language at {evidence}"))

    return rows


def render_report(paths: list[Path], events: list[Event]) -> str:
    scores = score_events(events)
    commands: Counter[str] = scores["commands"]  # type: ignore[assignment]
    phrases: list[Event] = scores["phrases"]  # type: ignore[assignment]
    corrections: list[Event] = scores["corrections"]  # type: ignore[assignment]
    sources: Counter[str] = scores["sources"]  # type: ignore[assignment]
    rows = proposal_rows(events, scores)

    lines = [
        "# Session To Skill Signal Report",
        "",
        "## Inputs",
        "",
    ]
    for path in paths:
        lines.append(f"- `{path}`")
    lines.extend([
        "",
        "## Corpus",
        "",
        f"- Files scanned: {len(sources)}",
        f"- Text events: {len(events)}",
        f"- Correction hints: {len(corrections)}",
        f"- Skill/rule phrase hints: {len(phrases)}",
        "",
        "## Repeated Commands",
        "",
    ])
    if commands:
        lines.extend(f"- {count}x `{command}`" for command, count in commands.most_common(10))
    else:
        lines.append("- None detected")

    lines.extend([
        "",
        "## First-Pass Candidates",
        "",
        "| Candidate | Evidence count | Rationale |",
        "| --- | ---: | --- |",
    ])
    if rows:
        lines.extend(f"| `{name}` | {count} | {reason} |" for name, count, reason in rows)
    else:
        lines.append("| No candidate | 0 | No repeated workflow passed the deterministic threshold |")

    lines.extend([
        "",
        "## Review Notes",
        "",
        "- Treat this as scaffolding for agent review, not a final decision.",
        "- Require 3 independent arcs or explicit user approval before creating a new skill.",
        "- Redact transcript details before sharing this report.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract reusable-skill signals from session logs.")
    parser.add_argument("paths", nargs="+", type=Path, help="Session files or directories to scan")
    parser.add_argument("--out", type=Path, help="Write markdown report to this path")
    args = parser.parse_args()

    events = extract_events(args.paths)
    report = render_report(args.paths, events)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
