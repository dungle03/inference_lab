"""Knowledge base container with utilities for rule and fact management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Set

from .models import Rule
from .utils import normalize_atom, parse_rule_text, split_atoms


@dataclass
class KnowledgeBase:
    """In-memory storage for rules and known facts."""

    rules: List[Rule] = field(default_factory=list)
    facts: Set[str] = field(default_factory=set)
    name: str = "knowledge-base"

    def __post_init__(self) -> None:
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._rules_by_id = {rule.id: rule for rule in self.rules}
        self._next_id = max(self._rules_by_id.keys(), default=0) + 1

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------
    def iter_rules(self) -> Iterator[Rule]:
        yield from sorted(self.rules, key=lambda rule: rule.id)

    def get_rule(self, rule_id: int) -> Rule:
        try:
            return self._rules_by_id[rule_id]
        except KeyError as exc:
            raise KeyError(f"Unknown rule id: {rule_id}") from exc

    def add_rule(
        self,
        premises: Sequence[str],
        conclusion: str,
        *,
        rule_id: Optional[int] = None,
    ) -> Rule:
        rid = self._allocate_rule_id(rule_id)
        rule = Rule.from_parts(rid, premises, conclusion)
        self.rules.append(rule)
        self._register_rule(rule)
        return rule

    def add_rule_from_text(self, text: str, *, rule_id: Optional[int] = None) -> Rule:
        premises, conclusion = parse_rule_text(text)
        return self.add_rule(premises, conclusion, rule_id=rule_id)

    def update_rule(
        self,
        rule_id: int,
        *,
        premises: Iterable[str] | None = None,
        conclusion: str | None = None,
    ) -> Rule:
        existing = self.get_rule(rule_id)
        updated = existing.with_updates(premises=premises, conclusion=conclusion)
        index = self.rules.index(existing)
        self.rules[index] = updated
        self._rules_by_id[rule_id] = updated
        return updated

    def remove_rule(self, rule_id: int) -> Rule:
        rule = self.get_rule(rule_id)
        self.rules.remove(rule)
        del self._rules_by_id[rule_id]
        return rule

    def load_rules_from_text(self, text: str) -> None:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            self.add_rule_from_text(stripped)

    def load_rules_from_file(self, path: Path) -> None:
        content = Path(path).read_text(encoding="utf-8")
        self.load_rules_from_text(content)

    def export_rules_text(self) -> str:
        lines = [rule.to_text() for rule in self.iter_rules()]
        return "\n".join(lines)

    def clear_rules(self) -> None:
        self.rules.clear()
        self._rebuild_index()

    def _allocate_rule_id(self, preferred: Optional[int]) -> int:
        if preferred is None:
            rid = self._next_id
            self._next_id += 1
            return rid
        if preferred in self._rules_by_id:
            raise ValueError(f"Rule id {preferred} already exists.")
        if preferred >= self._next_id:
            self._next_id = preferred + 1
        return preferred

    def _register_rule(self, rule: Rule) -> None:
        self._rules_by_id[rule.id] = rule

    # ------------------------------------------------------------------
    # Fact management
    # ------------------------------------------------------------------
    def load_facts_from_text(self, text: str) -> None:
        for atom in split_atoms(text):
            self.facts.add(atom)

    def set_facts(self, facts: Iterable[str]) -> None:
        self.facts = {normalize_atom(fact) for fact in facts if normalize_atom(fact)}

    def add_fact(self, fact: str) -> str:
        atom = normalize_atom(fact)
        if not atom:
            raise ValueError("Fact cannot be empty.")
        self.facts.add(atom)
        return atom

    def remove_fact(self, fact: str) -> None:
        atom = normalize_atom(fact)
        self.facts.discard(atom)

    def clear_facts(self) -> None:
        self.facts.clear()

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def clone(self) -> "KnowledgeBase":
        return KnowledgeBase(
            rules=list(self.iter_rules()),
            facts=set(self.facts),
            name=self.name,
        )

    def summary(self) -> str:
        rule_count = len(self.rules)
        fact_count = len(self.facts)
        return f"{self.name}: {rule_count} rule(s), {fact_count} fact(s)"

