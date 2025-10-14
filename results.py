"""Dataclasses describing reasoning outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class StepTrace:
    step: int
    rule_id: Optional[int]
    known_facts: List[str]
    thoa: List[int]
    remaining_rules: List[int]
    fired_rules: List[int]
    note: str | None = None


@dataclass
class ForwardResult:
    success: bool
    goals: List[str]
    final_facts: List[str]
    fired_rules: List[int]
    history: List[StepTrace] = field(default_factory=list)
    graph_files: Dict[str, Path] = field(default_factory=dict)


@dataclass
class BackwardResult:
    success: bool
    goals: List[str]
    final_known: List[str]
    used_rules: List[int]
    steps: List[str]
    graph_files: Dict[str, Path] = field(default_factory=dict)

