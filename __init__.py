"""Bidirectional inference toolkit supporting rule/fact management and graph rendering."""

from .knowledge_base import KnowledgeBase
from .models import Rule
from .results import ForwardResult, BackwardResult
from .forward import run_forward_inference
from .backward import run_backward_inference
from . import graphs
from . import web

__all__ = [
    "KnowledgeBase",
    "Rule",
    "ForwardResult",
    "BackwardResult",
    "run_forward_inference",
    "run_backward_inference",
    "graphs",
    "web",
]
