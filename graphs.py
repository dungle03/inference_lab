"""Graph utilities for visualising rule interactions."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple, Set

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
    *,
    given_facts: Iterable[str] = (),
) -> nx.DiGraph:
    graph = nx.DiGraph()
    known_set = set(known_facts)
    given_set = set(given_facts)
    goal_set = set(goal_facts)

    # Distinguish given facts vs derived facts for clarity
    for fact in given_set:
        graph.add_node(fact, type=FACT_NODE, role="given")
    for fact in known_set - given_set - goal_set:
        graph.add_node(fact, type=FACT_NODE, role="derived")
    for fact in goal_set:
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


def _apply_fact_style(
    dot: "Digraph | None", node: str, role: str | None, *, muted: bool = False
) -> None:
    if dot is None:
        return
    base_attrs = {
        "shape": "circle",
        "width": "0.7",
        "height": "0.7",
        "fixedsize": "true",
    }
    if muted:
        dot.node(
            node,
            node,
            fillcolor="#f8fafc",
            color="#cbd5e1",
            penwidth="1.0",
            **base_attrs,
        )
        return
    if role == "given":
        dot.node(
            node,
            node,
            fillcolor="#dbeafe",
            color="#1d4ed8",
            penwidth="2.0",
            **base_attrs,
        )
    elif role == "derived":
        dot.node(
            node,
            node,
            fillcolor="#e0f2fe",
            color="#0284c7",
            penwidth="1.8",
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


def _apply_rule_style(dot: "Digraph | None", node: str, *, muted: bool = False) -> None:
    if dot is None:
        return
    dot.node(
        node,
        node,
        shape="box",
        width="1.0",
        height="0.6",
        fillcolor="#f1f5f9" if not muted else "#f8fafc",
        color="#64748b" if not muted else "#cbd5e1",
        penwidth="1.8" if not muted else "1.0",
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
    highlight_nodes: Optional[Set[str]] = None,
    highlight_edges: Optional[Set[Tuple[str, str]]] = None,
) -> Optional[Path]:
    if not GRAPHVIZ_AVAILABLE:  # pragma: no cover
        return None

    dot = Digraph(comment="Inference graph")
    dot.attr(rankdir=rankdir)
    dot.attr(ratio=ratio)
    if size:
        dot.attr(size=size)
    dot.graph_attr.update(
        pad="0.4",
        bgcolor="#ffffff",
        splines="ortho",
        concentrate="true",
        ranksep="1.0",
        nodesep="0.6",
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
        style="filled,rounded",
        penwidth="1.2",
    )
    dot.edge_attr.update(
        arrowhead="vee",
        arrowsize="0.7",
        color="#94a3b8",
        penwidth="1.1",
        minlen="1",
    )

    for node in graph.nodes:
        node_type = graph.nodes[node].get("type")
        is_muted = bool(highlight_nodes) and node not in (highlight_nodes or set())
        if node_type == FACT_NODE:
            role = graph.nodes[node].get("role")
            _apply_fact_style(dot, node, role, muted=is_muted)
        else:
            _apply_rule_style(dot, node, muted=is_muted)

    hl_edges = highlight_edges or set()
    for source, target in graph.edges:
        if highlight_edges is not None and (source, target) not in hl_edges:
            dot.edge(source, target, color="#cbd5e1", arrowsize="0.6", penwidth="0.9")
        else:
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
    given_facts: Iterable[str] = (),
    highlight_rules: Optional[Iterable[int]] = None,
    used_only: bool = False,
) -> Optional[Path]:
    graph = build_fpg_graph(
        rules,
        known_facts=known_facts,
        goal_facts=goal_facts,
        given_facts=given_facts,
    )
    graph = build_fpg_graph(
        rules,
        known_facts=known_facts,
        goal_facts=goal_facts,
        given_facts=given_facts,
    )

    highlight_nodes: Set[str] | None = None
    highlight_edges: Set[Tuple[str, str]] | None = None
    if highlight_rules is not None:
        highlight_nodes = set()
        highlight_edges = set()
        rule_ids = {int(r) for r in highlight_rules}
        for rule in rules:
            if rule.id in rule_ids:
                rn = f"R{rule.id}"
                highlight_nodes.add(rn)
                for p in rule.premises:
                    highlight_nodes.add(p)
                    highlight_edges.add((p, rn))
                highlight_nodes.add(rule.conclusion)
                highlight_edges.add((rn, rule.conclusion))

    if used_only and highlight_nodes is not None:
        # Filter graph to highlighted subgraph only
        keep_nodes = set(highlight_nodes)
        graph = graph.subgraph(keep_nodes).copy()

    return render_graph(
        graph,
        output,
        rankdir="LR",
        ratio="auto",
        size=None,
        dpi=220,
        highlight_nodes=highlight_nodes,
        highlight_edges=highlight_edges,
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
