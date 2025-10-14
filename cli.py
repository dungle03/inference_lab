"""Interactive command line interface for the inference lab."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    PACKAGE_ROOT = Path(__file__).resolve().parent
    sys.path.insert(0, str(PACKAGE_ROOT.parent))
    from inference_lab.knowledge_base import KnowledgeBase  # type: ignore[no-redef]
    from inference_lab.forward import run_forward_inference  # type: ignore[no-redef]
    from inference_lab.backward import run_backward_inference  # type: ignore[no-redef]
    from inference_lab.utils import parse_rule_text, split_atoms, format_atoms  # type: ignore[no-redef]
    from inference_lab import graphs  # type: ignore[no-redef]
    from inference_lab.sample_data import (  # type: ignore[no-redef]
        TRIANGLE_RULES,
        TRIANGLE_DEFAULT_FACTS,
        TRIANGLE_DEFAULT_GOALS,
    )
else:
    from .knowledge_base import KnowledgeBase
    from .forward import run_forward_inference
    from .backward import run_backward_inference
    from .utils import parse_rule_text, split_atoms, format_atoms
    from . import graphs
    from .sample_data import (
        TRIANGLE_RULES,
        TRIANGLE_DEFAULT_FACTS,
        TRIANGLE_DEFAULT_GOALS,
    )


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = Path("inference_outputs")
TRIANGLE_RULES_FILE = ROOT_DIR / "triangle_rules.txt"


def load_triangle_sample() -> KnowledgeBase:
    kb = KnowledgeBase(name="triangle-demo")
    loaded = False
    if TRIANGLE_RULES_FILE.exists():
        try:
            kb.load_rules_from_file(TRIANGLE_RULES_FILE)
            loaded = True
        except Exception:
            kb.clear_rules()
    if not loaded:
        for rule in TRIANGLE_RULES:
            kb.add_rule_from_text(rule)
    kb.set_facts(TRIANGLE_DEFAULT_FACTS)
    return kb


def prompt(message: str) -> str:
    try:
        return input(message)
    except EOFError:  # pragma: no cover - interactive fallback
        print()
        return ""


def print_rules(kb: KnowledgeBase) -> None:
    print("\n=== Rules ===")
    if not kb.rules:
        print("No rules defined.")
        return
    for rule in kb.iter_rules():
        premises = ", ".join(rule.premises)
        print(f"R{rule.id}: {premises} -> {rule.conclusion}")


def print_facts(kb: KnowledgeBase) -> None:
    if kb.facts:
        print("Facts:", format_atoms(kb.facts))
    else:
        print("Facts: ∅")


def manage_rules(kb: KnowledgeBase) -> None:
    while True:
        print_rules(kb)
        print("\nRule menu: [a]dd, [e]dit, [d]elete, [c]lear, [q]uit")
        choice = prompt("Select option: ").strip().lower()
        if choice == "q":
            return
        if choice == "a":
            text = prompt("Enter rule (example: a, b -> c): ").strip()
            if not text:
                continue
            try:
                rule = kb.add_rule_from_text(text)
                print(f"Added R{rule.id}.")
            except Exception as exc:
                print(f"Error: {exc}")
        elif choice == "e":
            try:
                rid = int(prompt("Rule id to edit: "))
                rule = kb.get_rule(rid)
            except Exception as exc:
                print(f"Error: {exc}")
                continue
            new_text = prompt(f"New text for R{rid} [{rule.to_text()}]: ").strip()
            if not new_text:
                continue
            try:
                premises, conclusion = parse_rule_text(new_text)
                kb.update_rule(rid, premises=premises, conclusion=conclusion)
                print("Rule updated.")
            except Exception as exc:
                print(f"Error: {exc}")
        elif choice == "d":
            try:
                rid = int(prompt("Rule id to delete: ").strip())
                kb.remove_rule(rid)
                print("Rule removed.")
            except Exception as exc:
                print(f"Error: {exc}")
        elif choice == "c":
            confirm = prompt("Clear ALL rules? (y/N): ").strip().lower()
            if confirm == "y":
                kb.clear_rules()
                print("Rules cleared.")
        else:
            print("Unknown option.")


def manage_facts(kb: KnowledgeBase) -> None:
    while True:
        print("\nCurrent facts:")
        print_facts(kb)
        print("\nFact menu: [a]dd, [r]emove, [s]et, [c]lear, [q]uit")
        choice = prompt("Select option: ").strip().lower()
        if choice == "q":
            return
        if choice == "a":
            fact = prompt("Fact to add: ").strip()
            if fact:
                try:
                    kb.add_fact(fact)
                    print("Fact added.")
                except Exception as exc:
                    print(f"Error: {exc}")
        elif choice == "r":
            fact = prompt("Fact to remove: ").strip()
            if fact:
                kb.remove_fact(fact)
                print("Fact removed.")
        elif choice == "s":
            text = prompt("Facts (comma separated): ").strip()
            facts = split_atoms(text)
            kb.set_facts(facts)
            print("Facts replaced.")
        elif choice == "c":
            kb.clear_facts()
            print("Facts cleared.")
        else:
            print("Unknown option.")


def _collect_goals(default: Iterable[str]) -> List[str]:
    raw = prompt(f"Goals [{', '.join(default)}]: ").strip()
    return split_atoms(raw) if raw else list(default)


def _collect_strategy(default_structure: str = "stack") -> str:
    raw = prompt(f"Structure stack/queue [{default_structure}]: ").strip().lower()
    return raw or default_structure


def _collect_index_mode(default_mode: str = "min") -> str:
    raw = prompt(f"Index mode min/max [{default_mode}]: ").strip().lower()
    return raw or default_mode


def run_forward_cli(kb: KnowledgeBase) -> None:
    if not kb.rules:
        print("Cannot run inference: no rules.")
        return
    goals = _collect_goals(TRIANGLE_DEFAULT_GOALS)
    structure = _collect_strategy()
    mode = _collect_index_mode()
    try:
        result = run_forward_inference(
            kb,
            goals=goals,
            strategy=structure,
            index_mode=mode,
            make_graphs=True,
            output_dir=DEFAULT_OUTPUT_DIR,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return

    print("\n=== Forward inference result ===")
    print(f"Goals: {', '.join(result.goals)}")
    print(f"Success: {result.success}")
    print(f"Final facts: {', '.join(result.final_facts)}")
    print(f"Fired rules: {result.fired_rules or '∅'}")
    print("\nStep traces:")
    print(f"{'Step':<5} {'Rule':<6} {'Known':<25} {'THOA':<15} {'Remaining':<15} {'Fired'}")
    print("-" * 90)
    for trace in result.history:
        rule_repr = f"R{trace.rule_id}" if trace.rule_id is not None else "-"
        print(
            f"{trace.step:<5} {rule_repr:<6} "
            f"{format_atoms(trace.known_facts):<25} "
            f"{', '.join(f'R{rid}' for rid in trace.thoa) or '∅':<15} "
            f"{', '.join(f'R{rid}' for rid in trace.remaining_rules) or '∅':<15} "
            f"{', '.join(f'R{rid}' for rid in trace.fired_rules) or '∅'}"
        )
        if trace.note:
            print(f"      note: {trace.note}")

    if result.graph_files:
        for label, path in result.graph_files.items():
            print(f"{label.upper()} graph saved to: {path}")
    else:
        if not graphs.GRAPHVIZ_AVAILABLE:
            print("Graphviz not available; graphs were not generated.")


def run_backward_cli(kb: KnowledgeBase) -> None:
    if not kb.rules:
        print("Cannot run inference: no rules.")
        return
    goals = _collect_goals(TRIANGLE_DEFAULT_GOALS)
    mode = _collect_index_mode()
    try:
        result = run_backward_inference(
            kb,
            goals=goals,
            index_mode=mode,
            make_graph=True,
            output_dir=DEFAULT_OUTPUT_DIR,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return

    print("\n=== Backward inference result ===")
    print(f"Goals: {', '.join(result.goals)}")
    print(f"Success: {result.success}")
    print(f"Final known facts: {', '.join(result.final_known)}")
    print(f"Used rules: {result.used_rules or '∅'}")
    print("\nTrace:")
    for line in result.steps:
        print(line)

    if result.graph_files:
        for label, path in result.graph_files.items():
            print(f"{label.upper()} graph saved to: {path}")
    else:
        if not graphs.GRAPHVIZ_AVAILABLE:
            print("Graphviz not available; graphs were not generated.")


def render_graphs_cli(kb: KnowledgeBase) -> None:
    if not kb.rules:
        print("No rules to render.")
        return
    out_dir = DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    fpg_path = graphs.render_fpg(
        list(kb.iter_rules()),
        known_facts=kb.facts,
        goal_facts=TRIANGLE_DEFAULT_GOALS,
        output=out_dir / "manual_fpg.png",
    )
    rpg_path = graphs.render_rpg(
        list(kb.iter_rules()),
        output=out_dir / "manual_rpg.png",
    )
    if fpg_path:
        print(f"FPG graph saved to: {fpg_path}")
    if rpg_path:
        print(f"RPG graph saved to: {rpg_path}")
    if not (fpg_path or rpg_path):
        print("Graphs were not generated (Graphviz missing?).")


def main(argv: Optional[List[str]] = None) -> int:
    kb = load_triangle_sample()
    argv = argv or sys.argv[1:]
    if "--no-sample" in argv:
        kb = KnowledgeBase()

    while True:
        print("\n=== Inference Lab ===")
        print(kb.summary())
        print_rules(kb)
        print_facts(kb)
        print(
            "\nMenu:\n"
            " 1. Manage rules\n"
            " 2. Manage facts\n"
            " 3. Run forward inference\n"
            " 4. Run backward inference\n"
            " 5. Render graphs (FPG & RPG)\n"
            " 6. Reload triangle sample\n"
            " 0. Exit\n"
        )
        choice = prompt("Select option: ").strip()
        if choice == "0":
            return 0
        if choice == "1":
            manage_rules(kb)
        elif choice == "2":
            manage_facts(kb)
        elif choice == "3":
            run_forward_cli(kb)
        elif choice == "4":
            run_backward_cli(kb)
        elif choice == "5":
            render_graphs_cli(kb)
        elif choice == "6":
            kb = load_triangle_sample()
            print("Triangle sample reloaded.")
        else:
            print("Unknown option.")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
