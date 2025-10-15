"""Utility helpers for parsing rules and formatting reasoning output."""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence


ATOM_SPLIT_PATTERN = re.compile(r"\s*(?:,|&|\?|\^|and)\s*", re.IGNORECASE)


def normalize_atom(atom: str) -> str:
    return atom.strip()


def split_atoms(raw: str) -> List[str]:
    if not raw:
        return []
    tokens = ATOM_SPLIT_PATTERN.split(raw.strip())
    return [normalize_atom(token) for token in tokens if normalize_atom(token)]


def parse_rule_text(raw: str) -> tuple[List[str], str]:
    text = raw.strip()
    if not text:
        raise ValueError("Rule text is empty.")
    # Normalize common arrow variants and strip control chars
    cleaned = re.sub(r"[\u0000-\u001F\u007F]", "", text)
    normalized = cleaned.replace("=>", "->").replace("→", "->").replace(":>", "->")
    if "->" in normalized:
        left, right = normalized.split("->", 1)
    elif "" in text:
        # Legacy separator from some editors/copy-paste
        left, right = text.split("", 1)
    else:
        raise ValueError("Rule must contain an arrow like '->' (example: a & b -> c).")
    premises = split_atoms(left)
    conclusion = normalize_atom(right)
    if not premises:
        raise ValueError("Rule is missing premises.")
    if not conclusion:
        raise ValueError("Rule is missing conclusion.")
    return premises, conclusion


def format_atoms(items: Iterable[str]) -> str:
    data = sorted(set(item for item in items if item))
    return ", ".join(data) if data else "∅"


def ensure_choice(value: str, choices: Sequence[str], *, label: str) -> str:
    lowered = value.strip().lower()
    normalized = [choice.lower() for choice in choices]
    if lowered not in normalized:
        readable = ", ".join(choices)
        raise ValueError(f"{label} must be one of: {readable}")
    return choices[normalized.index(lowered)]
