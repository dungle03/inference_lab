"""Sample datasets bundled with the inference lab."""

from __future__ import annotations

TRIANGLE_RULES = [
    "a ^ b ^ C -> c",
    "a ^ b ^ ma -> c",
    "a ^ b ^ mb -> c",
    "A ^ B -> C",
    "a ^ hc -> B",
    "b ^ hc -> A",
    "a ^ R -> A",
    "b ^ R -> B",
    "a ^ b ^ c -> P",
    "a ^ b ^ c -> p",
    "a ^ b ^ c -> mc",
    "a ^ ha -> S",
    "a ^ b ^ C -> S",
    "a ^ b ^ c ^ p -> S",
    "b ^ S -> hb",
    "S ^ p -> r",
]

TRIANGLE_DEFAULT_FACTS = {"a", "b", "c"}
TRIANGLE_DEFAULT_GOALS = {"r"}
