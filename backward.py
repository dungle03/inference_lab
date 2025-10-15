"""Backward-chaining reasoning."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .knowledge_base import KnowledgeBase
from .models import Rule
from .results import BackwardResult
from .utils import ensure_choice, normalize_atom
from . import graphs

BACKWARD_INDEX_MODES = ("min", "max")


def _build_lookup(rules: Sequence[Rule]) -> Dict[str, List[Rule]]:
    mapping: Dict[str, List[Rule]] = {}
    for rule in rules:
        mapping.setdefault(rule.conclusion, []).append(rule)
    return mapping


def run_backward_inference(
    kb: KnowledgeBase,
    *,
    goals: Iterable[str],
    index_mode: str = "min",
    initial_facts: Optional[Iterable[str]] = None,
    output_dir: Optional[Path] = None,
    make_graph: bool = True,
) -> BackwardResult:
    mode = ensure_choice(index_mode, BACKWARD_INDEX_MODES, label="index_mode")

    rules = list(kb.iter_rules())
    if not rules:
        raise ValueError("Knowledge base has no rules.")

    goal_list = [normalize_atom(goal) for goal in goals if normalize_atom(goal)]
    if not goal_list:
        raise ValueError("At least one goal fact is required.")

    known: Set[str] = (
        {normalize_atom(f) for f in initial_facts if normalize_atom(f)}
        if initial_facts is not None
        else set(kb.facts)
    )
    used_rules: List[int] = []
    steps: List[str] = []

    rules_by_conclusion = _build_lookup(rules)
    visiting: Set[str] = set()

    def prove(goal: str, depth: int = 0) -> bool:
        indent = "  " * depth
        if goal in known:
            steps.append(f"{indent}- Mục tiêu '{goal}' đã có trong tập tri thức.")
            return True
        if goal in visiting:
            steps.append(f"{indent}- Phát hiện vòng lặp khi chứng minh '{goal}'.")
            return False

        candidates = rules_by_conclusion.get(goal, [])
        if not candidates:
            steps.append(f"{indent}- Không có luật nào kết luận '{goal}'.")
            return False

        ordered = sorted(
            candidates,
            key=lambda item: item.id,
            reverse=(mode == "max"),
        )
        visiting.add(goal)
        steps.append(
            f"{indent}- Đang xét {len(ordered)} luật cho mục tiêu '{goal}' "
            f"(ưu tiên: {mode})."
        )

        for rule in ordered:
            steps.append(f"{indent}  → Thử luật R{rule.id}: {rule.to_text()}")
            success = True
            for premise in rule.premises:
                steps.append(f"{indent}    • Chứng minh tiền đề '{premise}'")
                if not prove(premise, depth + 2):
                    success = False
                    steps.append(
                        f"{indent}    x Không chứng minh được '{premise}' nên bỏ luật R{rule.id}."
                    )
                    break
            if success:
                known.add(goal)
                used_rules.append(rule.id)
                steps.append(
                    f"{indent}  ✓ Mục tiêu '{goal}' được chứng minh nhờ R{rule.id}."
                )
                visiting.remove(goal)
                return True

        visiting.remove(goal)
        steps.append(f"{indent}- Không chứng minh được '{goal}'.")
        return False

    overall_success = True
    for top_goal in goal_list:
        if top_goal in known:
            steps.append(f"Mục tiêu '{top_goal}' đã thỏa từ đầu.")
            continue
        steps.append(f"\n=== BẮT ĐẦU CHỨNG MINH MỤC TIÊU '{top_goal}' ===")
        if not prove(top_goal, depth=1):
            overall_success = False
            steps.append(f"!!! Thất bại khi chứng minh '{top_goal}'.")
            break
        steps.append(f"+++ Hoàn tất mục tiêu '{top_goal}'.")

    graph_files: Dict[str, Path] = {}
    if make_graph:
        out_dir = Path(output_dir or "inference_outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        fpg_path = out_dir / "backward_fpg.svg"
        rendered = graphs.render_fpg(
            rules,
            known_facts=known,
            goal_facts=goal_list,
            output=fpg_path,
            given_facts=set(kb.facts),
        )
        if rendered:
            graph_files["fpg"] = rendered

    return BackwardResult(
        success=overall_success and set(goal_list).issubset(known),
        goals=goal_list,
        final_known=sorted(known),
        used_rules=used_rules,
        steps=steps,
        graph_files=graph_files,
    )
