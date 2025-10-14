"""Core data structures used by the inference toolkit."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Tuple


def _dedupe_preserve_order(items: Iterable[str]) -> Tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


@dataclass(frozen=True)
class Rule:
    """Inference rule represented by an identifier, premises and conclusion."""

    id: int
    premises: Tuple[str, ...]
    conclusion: str

    @classmethod
    def from_parts(cls, rule_id: int, premises: Iterable[str], conclusion: str) -> "Rule":
        return cls(rule_id, _dedupe_preserve_order(premises), conclusion.strip())

    def with_updates(
        self,
        *,
        premises: Iterable[str] | None = None,
        conclusion: str | None = None,
    ) -> "Rule":
        return replace(
            self,
            premises=(
                _dedupe_preserve_order(premises)
                if premises is not None
                else self.premises
            ),
            conclusion=conclusion.strip() if conclusion is not None else self.conclusion,
        )

    def to_text(self, joiner: str = " ^ ") -> str:
        left = joiner.join(self.premises)
        return f"{left} -> {self.conclusion}"
