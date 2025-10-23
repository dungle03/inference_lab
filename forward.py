"""Forward-chaining reasoning strategies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .knowledge_base import KnowledgeBase
from .models import Rule
from .results import ForwardResult, StepTrace
from .utils import ensure_choice, format_atoms, normalize_atom
from . import graphs

FORWARD_STRUCTURES = ("stack", "queue")
FORWARD_INDEX_MODES = ("min", "max")


def _collect_rules(kb: KnowledgeBase) -> List[Rule]:
    return list(kb.iter_rules())


def _enqueue_candidates(
    thoa: List[int],
    remaining: Set[int],
    known: Set[str],
    rules: Sequence[Rule],
    *,
    structure: str,
    index_mode: str,
) -> None:
    candidates: List[int] = []
    existing = set(thoa)
    for rule in rules:
        if rule.id not in remaining:
            continue
        if rule.id in existing:
            continue
        if set(rule.premises).issubset(known) and rule.conclusion not in known:
            candidates.append(rule.id)

    if not candidates:
        return

    if structure == "stack":
        candidates.sort(reverse=index_mode == "min")
    else:  # queue
        candidates.sort(reverse=index_mode == "max")

    for rid in candidates:
        thoa.append(rid)


def _select_rule(thoa: List[int], *, structure: str) -> int:
    if not thoa:
        raise ValueError("No candidates available.")
    if structure == "stack":
        return thoa.pop()
    return thoa.pop(0)


def run_forward_inference(
    kb: KnowledgeBase,
    *,
    goals: Iterable[str],
    strategy: str = "stack",
    index_mode: str = "min",
    initial_facts: Optional[Iterable[str]] = None,
    output_dir: Optional[Path] = None,
    make_graphs: bool = False,
) -> ForwardResult:
    structure = ensure_choice(strategy, FORWARD_STRUCTURES, label="strategy")
    selection = ensure_choice(index_mode, FORWARD_INDEX_MODES, label="index_mode")

    rules = _collect_rules(kb)
    if not rules:
        raise ValueError("Knowledge base has no rules.")

    goal_set = {normalize_atom(goal) for goal in goals if normalize_atom(goal)}
    if not goal_set:
        raise ValueError("At least one goal fact is required.")

    known: Set[str] = (
        {normalize_atom(f) for f in initial_facts if normalize_atom(f)}
        if initial_facts is not None
        else set(kb.facts)
    )

    thoa: List[int] = []
    fired: List[int] = []
    remaining: Set[int] = {rule.id for rule in rules}
    rule_index: Dict[int, Rule] = {rule.id: rule for rule in rules}
    history: List[StepTrace] = []

    _enqueue_candidates(
        thoa, remaining, known, rules, structure=structure, index_mode=selection
    )
    history.append(
        StepTrace(
            step=0,
            rule_id=None,
            known_facts=sorted(known),
            thoa=list(thoa),
            remaining_rules=sorted(remaining),
            fired_rules=list(fired),
            note="Trạng thái ban đầu",
        )
    )

    step = 0
    while thoa and not goal_set.issubset(known):
        step += 1
        rule_id = _select_rule(thoa, structure=structure)
        rule = rule_index[rule_id]
        fired.append(rule_id)
        remaining.discard(rule_id)
        known.add(rule.conclusion)

        _enqueue_candidates(
            thoa, remaining, known, rules, structure=structure, index_mode=selection
        )

        history.append(
            StepTrace(
                step=step,
                rule_id=rule_id,
                known_facts=sorted(known),
                thoa=list(thoa),
                remaining_rules=sorted(remaining),
                fired_rules=list(fired),
                note=f"Suy ra {rule.conclusion}",
            )
        )

    success = goal_set.issubset(known)
    if not success and not thoa:
        history.append(
            StepTrace(
                step=step + 1,
                rule_id=None,
                known_facts=sorted(known),
                thoa=list(thoa),
                remaining_rules=sorted(remaining),
                fired_rules=list(fired),
                note="Không còn luật khả dụng",
            )
        )

    graph_files: Dict[str, Path] = {}
    if make_graphs:
        out_dir = Path(output_dir or "inference_outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        fpg_path = out_dir / "forward_fpg.svg"
        rpg_path = out_dir / "forward_rpg.svg"
        # FPG chỉ hiển thị fact nodes, phân biệt GT (given) và fact suy ra
        fpg_rendered = graphs.render_fpg(
            rules,
            known_facts=known,
            goal_facts=goal_set,
            output=fpg_path,
            given_facts=set(kb.facts),
        )
        rpg_rendered = graphs.render_rpg(rules, output=rpg_path)
        if fpg_rendered:
            graph_files["fpg"] = fpg_rendered
        if rpg_rendered:
            graph_files["rpg"] = rpg_rendered

    return ForwardResult(
        success=success,
        goals=sorted(goal_set),
        final_facts=sorted(known),
        fired_rules=fired,
        history=history,
        graph_files=graph_files,
    )
