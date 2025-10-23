"""Routes module for inference_lab web application.

Contains two blueprints:
- lab_bp: Original lab interface for developers/researchers
- medical_bp: New medical diagnosis interface for end users
"""

from .lab_routes import lab_bp
from .medical_routes import medical_bp

__all__ = ["lab_bp", "medical_bp"]
