"""Graph utilities for visualising rule interactions."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx

try:
    from graphviz import Digraph

    GRAPHVIZ_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    GRAPHVIZ_AVAILABLE = False
    Digraph = None  # type: ignore[assignment]

from .models import Rule

FACT_NODE = "fact"
RULE_NODE = "rule"


def build_fpg_graph(
    rules: Sequence[Rule],
    known_facts: Iterable[str] = (),
    goal_facts: Iterable[str] = (),
) -> nx.DiGraph:
    graph = nx.DiGraph()
    for fact in known_facts:
        graph.add_node(fact, type=FACT_NODE, role="known")
    for fact in goal_facts:
        graph.add_node(fact, type=FACT_NODE, role="goal")

    for rule in rules:
        rule_node = f"R{rule.id}"
        graph.add_node(rule_node, type=RULE_NODE, rule_id=rule.id)
        graph.add_node(rule.conclusion, type=FACT_NODE)
        graph.add_edge(rule_node, rule.conclusion)
        for premise in rule.premises:
            graph.add_node(premise, type=FACT_NODE)
            graph.add_edge(premise, rule_node)
    return graph


def build_rpg_graph(rules: Sequence[Rule]) -> nx.DiGraph:
    """Construct a rule precedence graph (RPG)."""

    graph = nx.DiGraph()
    conclusions: Dict[str, list[int]] = {}

    for rule in rules:
        node = f"R{rule.id}"
        graph.add_node(node, type=RULE_NODE, label=node)
        conclusions.setdefault(rule.conclusion, []).append(rule.id)

    for rule in rules:
        source = f"R{rule.id}"
        for premise in rule.premises:
            for producer in conclusions.get(premise, []):
                target = f"R{producer}"
                if source != target:
                    graph.add_edge(target, source)
    return graph


def _apply_fact_style(dot: "Digraph | None", node: str, role: str | None) -> None:
    if dot is None:
        return
    base_attrs = {
        "shape": "circle",
        "width": "0.8",
        "height": "0.8",
        "fixedsize": "true",
    }
    if role == "known":
        dot.node(
            node,
            node,
            fillcolor="#dbeafe",
            color="#1d4ed8",
            penwidth="2.0",
            **base_attrs,
        )
    elif role == "goal":
        dot.node(
            node,
            node,
            fillcolor="#d1fae5",
            color="#059669",
            penwidth="2.5",
            **base_attrs,
        )
    else:
        dot.node(
            node,
            node,
            fillcolor="#fef3c7",
            color="#d97706",
            penwidth="1.8",
            **base_attrs,
        )


def _apply_rule_style(dot: "Digraph | None", node: str) -> None:
    if dot is None:
        return
    dot.node(
        node,
        node,
        shape="box",
        width="1.0",
        height="0.6",
        fillcolor="#f1f5f9",
        color="#64748b",
        penwidth="1.8",
        margin="0.12,0.08",
        fixedsize="true",
    )


def _group_nodes_by_rank(dot: "Digraph", graph: nx.DiGraph) -> None:
    """Group nodes into layers for cleaner left-to-right flow."""

    levels: Dict[str, int] = {}
    queue: deque[Tuple[str, int]] = deque()

    sources = [node for node in graph.nodes if graph.in_degree(node) == 0]
    if not sources:
        sources = list(graph.nodes)

    for node in sources:
        levels[node] = 0
        queue.append((node, 0))

    while queue:
        current, level = queue.popleft()
        for successor in graph.successors(current):
            next_level = level + 1
            if successor not in levels or next_level > levels[successor]:
                levels[successor] = next_level
                queue.append((successor, next_level))

    for node in graph.nodes:
        levels.setdefault(node, 0)

    groups: DefaultDict[int, List[str]] = DefaultDict(list)
    for node, level in levels.items():
        groups[level].append(node)

    for level in sorted(groups):
        nodes = groups[level]
        if len(nodes) <= 1:
            continue
        nodes.sort(key=lambda n: (graph.nodes[n].get("type") != FACT_NODE, n))
        with dot.subgraph(name=f"rank_{level}") as same_rank:
            same_rank.attr(rank="same")
            for node in nodes:
                same_rank.node(node)


def render_graph(
    graph: nx.DiGraph,
    filename: Path,
    *,
    rankdir: str = "LR",
    ratio: str = "auto",
    size: str | None = None,
    dpi: int = 160,
) -> Optional[Path]:
    if not GRAPHVIZ_AVAILABLE:  # pragma: no cover
        return None

    dot = Digraph(comment="Inference graph")
    dot.attr(rankdir=rankdir)
    dot.attr(ratio=ratio)
    if size:
        dot.attr(size=size)
    dot.graph_attr.update(
        pad="0.5",
        bgcolor="#ffffff",
        splines="polyline",
        ranksep="1.5",
        nodesep="1.2",
        fontname="Arial",
        fontsize="14",
        labelloc="t",
        overlap="false",
        outputorder="edgesfirst",
    )
    dot.graph_attr.update(dpi=str(dpi))
    dot.node_attr.update(
        fontname="Arial",
        fontsize="12",
        style="filled",
        penwidth="1.2",
    )
    dot.edge_attr.update(
        arrowhead="vee",
        arrowsize="0.9",
        color="#555555",
        penwidth="1.3",
        minlen="1",
    )

    for node in graph.nodes:
        node_type = graph.nodes[node].get("type")
        if node_type == FACT_NODE:
            role = graph.nodes[node].get("role")
            _apply_fact_style(dot, node, role)
        else:
            _apply_rule_style(dot, node)

    for source, target in graph.edges:
        dot.edge(source, target)

    _group_nodes_by_rank(dot, graph)

    filename = Path(filename)
    base, ext = filename.stem, filename.suffix
    fmt = ext.lstrip(".") or "png"
    output = dot.render(filename.with_suffix(""), format=fmt, cleanup=True)
    return Path(output)


def render_fpg(
    rules: Sequence[Rule],
    *,
    known_facts: Iterable[str] = (),
    goal_facts: Iterable[str] = (),
    output: Path,
) -> Optional[Path]:
    graph = build_fpg_graph(rules, known_facts=known_facts, goal_facts=goal_facts)
    return render_graph(
        graph,
        output,
        rankdir="LR",
        ratio="auto",
        size=None,
        dpi=220,
    )


def render_rpg(
    rules: Sequence[Rule],
    *,
    output: Path,
) -> Optional[Path]:
    graph = build_rpg_graph(rules)
    return render_graph(
        graph,
        output,
        rankdir="LR",
        ratio="auto",
        size=None,
        dpi=220,
    )
