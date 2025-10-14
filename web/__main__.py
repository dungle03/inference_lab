"""Module entry point for running the inference lab web app."""

from __future__ import annotations

import os

from . import create_app


def main() -> None:  # pragma: no cover - CLI entry point
    app = create_app()
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", os.environ.get("PORT", "5000")))
    debug = os.environ.get("FLASK_DEBUG") in {"1", "true", "True"}
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":  # pragma: no cover
    main()
