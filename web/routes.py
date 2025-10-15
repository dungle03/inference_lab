"""Flask routes for the inference lab web UI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from flask import (
    Blueprint,
    Flask,
    current_app,
    jsonify,
    render_template,
    request,
    url_for,
)

from inference_lab.backward import run_backward_inference
from inference_lab.forward import run_forward_inference
from inference_lab.graphs import GRAPHVIZ_AVAILABLE
from inference_lab.knowledge_base import KnowledgeBase
from inference_lab.results import BackwardResult, ForwardResult, StepTrace
from inference_lab.sample_data import (
    TRIANGLE_DEFAULT_FACTS,
    TRIANGLE_DEFAULT_GOALS,
    TRIANGLE_RULES,
)
from inference_lab.utils import split_atoms


def register_routes(app: Flask) -> None:
    blueprint = Blueprint("inference_web", __name__)

    @blueprint.get("/")
    def index() -> str:
        sample_payload = {
            "rules": TRIANGLE_RULES,
            "facts": sorted(TRIANGLE_DEFAULT_FACTS),
            "goals": sorted(TRIANGLE_DEFAULT_GOALS),
        }
        return render_template(
            "index.html",
            sample=sample_payload,
            graphviz_available=GRAPHVIZ_AVAILABLE,
            current_year=datetime.now().year,
        )

    @blueprint.post("/api/infer")
    def api_infer():
        payload = request.get_json(silent=True) or {}
        try:
            request_data = _parse_request_payload(payload)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

        session_id = uuid4().hex
        output_root: Path = Path(current_app.config["GRAPH_OUTPUT_ROOT"])
        output_dir = output_root / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if request_data["mode"] == "forward":
                result = _handle_forward(request_data, output_dir)
            else:
                result = _handle_backward(request_data, output_dir)
        except ValueError as exc:
            # domain validation from inference layer
            _cleanup_dir(output_dir)
            return jsonify({"ok": False, "error": str(exc)}), 400

        response = {"ok": True, "mode": request_data["mode"], "result": result}

        _cleanup_old_directories(
            output_root, keep=current_app.config.get("GRAPH_MAX_HISTORY", 12)
        )
        return jsonify(response)

    app.register_blueprint(blueprint)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_request_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    mode = (payload.get("mode") or "forward").strip().lower()
    if mode not in {"forward", "backward"}:
        raise ValueError("Mode must be 'forward' hoặc 'backward'.")

    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list):
        raise ValueError("Trường 'rules' phải là danh sách chuỗi.")
    rules = [str(rule).strip() for rule in raw_rules if str(rule).strip()]

    raw_facts = payload.get("facts", [])
    if isinstance(raw_facts, str):
        facts = split_atoms(raw_facts)
    elif isinstance(raw_facts, list):
        facts = [str(item).strip() for item in raw_facts if str(item).strip()]
    else:
        raise ValueError("Trường 'facts' phải là danh sách hoặc chuỗi.")

    raw_goals = payload.get("goals", [])
    if isinstance(raw_goals, str):
        goals = split_atoms(raw_goals)
    elif isinstance(raw_goals, list):
        goals = [str(item).strip() for item in raw_goals if str(item).strip()]
    else:
        raise ValueError("Trường 'goals' phải là danh sách hoặc chuỗi.")

    options = payload.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError("Trường 'options' phải là object JSON.")

    return {
        "mode": mode,
        "rules": rules,
        "facts": facts,
        "goals": goals,
        "options": options,
    }


def _build_kb(rules: Iterable[str], facts: Iterable[str]) -> KnowledgeBase:
    kb = KnowledgeBase(name="web-session")
    for text in rules:
        kb.add_rule_from_text(text)
    kb.set_facts(facts)
    return kb


def _handle_forward(request_data: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    options = request_data["options"]
    structure = (options.get("structure") or "stack").lower()
    index_mode = (options.get("index_mode") or "min").lower()

    kb = _build_kb(request_data["rules"], request_data["facts"])
    result = run_forward_inference(
        kb,
        goals=request_data["goals"],
        strategy=structure,
        index_mode=index_mode,
        make_graphs=True,
        output_dir=output_dir,
    )
    return _serialize_forward_result(result, output_dir)


def _handle_backward(request_data: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    options = request_data["options"]
    index_mode = (options.get("index_mode") or "min").lower()

    kb = _build_kb(request_data["rules"], request_data["facts"])
    result = run_backward_inference(
        kb,
        goals=request_data["goals"],
        index_mode=index_mode,
        make_graph=True,
        output_dir=output_dir,
    )
    return _serialize_backward_result(result, output_dir)


def _serialize_forward_result(
    result: ForwardResult, output_dir: Path
) -> Dict[str, Any]:
    return {
        "success": result.success,
        "goals": result.goals,
        "finalFacts": result.final_facts,
        "firedRules": result.fired_rules,
        "history": [_trace_to_dict(trace) for trace in result.history],
        "graphs": _graph_urls(result.graph_files, output_dir),
    }


def _serialize_backward_result(
    result: BackwardResult, output_dir: Path
) -> Dict[str, Any]:
    return {
        "success": result.success,
        "goals": result.goals,
        "finalKnown": result.final_known,
        "usedRules": result.used_rules,
        "steps": result.steps,
        "graphs": _graph_urls(result.graph_files, output_dir),
    }


def _trace_to_dict(trace: StepTrace) -> Dict[str, Any]:
    return {
        "step": trace.step,
        "rule": trace.rule_id,
        "known": trace.known_facts,
        "thoa": trace.thoa,
        "remaining": trace.remaining_rules,
        "fired": trace.fired_rules,
        "note": trace.note,
    }


def _graph_urls(graph_files: Dict[str, Path], output_dir: Path) -> Dict[str, str]:
    urls: Dict[str, str] = {}
    for key, path in graph_files.items():
        urls[key] = _static_url(path)
    return urls


def _static_url(path: Path) -> str:
    try:
        relative = path.relative_to(Path(current_app.static_folder))
    except ValueError:
        # fallback: recompute from output directory
        relative = path
    return url_for("static", filename=str(relative).replace("\\", "/"))


def _cleanup_dir(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        try:
            if child.is_file():
                child.unlink()
            else:
                _cleanup_dir(child)
        except OSError:
            continue
    try:
        path.rmdir()
    except OSError:
        pass


def _cleanup_old_directories(root: Path, *, keep: int = 10) -> None:
    if keep <= 0:
        keep = 1
    if not root.exists():
        return
    entries: List[Tuple[float, Path]] = []
    for child in root.iterdir():
        if child.is_dir():
            try:
                entries.append((child.stat().st_mtime, child))
            except OSError:
                continue
    entries.sort(reverse=True)
    for _, folder in entries[keep:]:
        _cleanup_dir(folder)
