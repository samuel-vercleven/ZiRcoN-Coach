"""V0.1 presentation contracts layered over immutable frozen analyzers."""

ANALYZER_VERSIONS = {
    "death": "death_analyzer_v11",
    "tempo": "jungle_tempo_pathing_v17",
    "objectives": "objective_analyzer_v20",
    "resets": "recall_reset_v21",
    "build": "itemization_v22_phase1",
}

# Presentation versions intentionally move independently from source versions.
ANALYZER_CACHE_VERSIONS = {
    "death": "death_analyzer_v11__v01_adapter_v2",
    "tempo": "jungle_tempo_pathing_v17__v01_adapter_v2",
    "objectives": "objective_analyzer_v20__v01_adapter_v2",
    "resets": "recall_reset_v21__v01_adapter_v2",
    "build": "itemization_v22_phase1__v01_adapter_v2",
}

ANALYZER_ORDER = tuple(ANALYZER_VERSIONS)
SOLO_QUEUE_ID = 420
