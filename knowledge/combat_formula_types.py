"""Typed evaluation outcomes for Phase 2G."""
from dataclasses import dataclass, field
from typing import Any

COMBAT_FORMULA_TYPES_VERSION = "combat_formula_types_phase2g_v1"
RESOLVED = "RESOLVED"
RESOLVED_WITH_WARNINGS = "RESOLVED_WITH_WARNINGS"
PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
UNSUPPORTED_CLASS = "UNSUPPORTED_CLASS"
UNSUPPORTED_SIGNATURE = "UNSUPPORTED_SIGNATURE"
MISSING_CONTEXT = "MISSING_CONTEXT"
MISSING_DATA_VALUE = "MISSING_DATA_VALUE"
AMBIGUOUS_DATA_VALUE = "AMBIGUOUS_DATA_VALUE"
UNRESOLVED_STAT_REFERENCE = "UNRESOLVED_STAT_REFERENCE"
UNRESOLVED_STAT_OWNER = "UNRESOLVED_STAT_OWNER"
INVALID_SPELL_RANK = "INVALID_SPELL_RANK"
NON_NUMERIC_RESULT = "NON_NUMERIC_RESULT"
NAMED_CALCULATION_NOT_FOUND = "NAMED_CALCULATION_NOT_FOUND"
NAMED_CALCULATION_AMBIGUOUS = "NAMED_CALCULATION_AMBIGUOUS"
CYCLE_DETECTED = "CYCLE_DETECTED"
MAX_RECURSION_DEPTH = "MAX_RECURSION_DEPTH"
MALFORMED_NODE = "MALFORMED_NODE"
SOURCE_VERSION_MISMATCH = "SOURCE_VERSION_MISMATCH"

@dataclass
class EvaluationResult:
    status: str
    value: float | None = None
    raw_class: str | None = None
    graph_path: str = ""
    calculation_key: str = ""
    dependencies: list[str] = field(default_factory=list)
    required_context: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    unresolved_reasons: list[str] = field(default_factory=list)
    child_results: list["EvaluationResult"] = field(default_factory=list)
    known_partial_value: float | None = None
