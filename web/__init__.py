"""Web interface for the inference lab toolkit."""

from __future__ import annotations

import atexit
from pathlib import Path

from flask import Flask, redirect, render_template

from .routes import lab_bp, medical_bp


def _remove_tree(path: Path) -> None:
    """Best-effort recursive deletion helper."""
    if not path.exists():
        return
    for child in path.iterdir():
        try:
            if child.is_dir():
                _remove_tree(child)
            else:
                try:
                    child.unlink()
                except FileNotFoundError:
                    pass
        except OSError:
            continue
    try:
        path.rmdir()
    except OSError:
        pass


def _register_shutdown_cleanup(graph_root: Path) -> None:
    """Register cleanup handler that runs when the interpreter exits."""

    def _clear_generated() -> None:
        if not graph_root.exists():
            return
        for child in graph_root.iterdir():
            try:
                if child.is_dir():
                    _remove_tree(child)
                else:
                    try:
                        child.unlink()
                    except FileNotFoundError:
                        pass
            except OSError:
                continue

    atexit.register(_clear_generated)


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent
    static_dir = base_dir / "static"
    template_dir = base_dir / "templates"
    static_dir.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        static_folder=str(static_dir),
        template_folder=str(template_dir),
    )
    app.config.setdefault("MAX_CONTENT_LENGTH", 4 * 1024 * 1024)  # 4MB uploads guard

    graph_root = static_dir / "generated"
    graph_root.mkdir(parents=True, exist_ok=True)
    app.config["GRAPH_OUTPUT_ROOT"] = graph_root
    app.config.setdefault("GRAPH_MAX_HISTORY", 12)

    # Register blueprints
    app.register_blueprint(lab_bp)
    app.register_blueprint(medical_bp)

    # Root route - show home page with options
    @app.route("/")
    def index():
        return render_template("home.html", current_year=2025)

    _register_shutdown_cleanup(graph_root)
    return app


__all__ = ["create_app"]
