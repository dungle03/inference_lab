"""Compatibility entry point for running the web interface."""

from __future__ import annotations

import os

from inference_lab.web import create_app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", os.environ.get("PORT", "5000")))
    debug_flag = os.environ.get("FLASK_DEBUG") in {"1", "true", "True"}
    app.run(host=host, port=port, debug=debug_flag)
