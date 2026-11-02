# Research methodology

The debugging workflow is inspired by TreeInstruct's hierarchical,
question-led interaction. AgentTutor extends that approach with course-aware
tutoring, retrieval, citations, adaptive hint policy, and persistent student
models.

The implementation must not be described as a reproduction or effectiveness
claim without a completed evaluation run. The evaluation package defines
conditions A through E and summarizes recorded observations only. Missing
observations are omitted rather than converted to positive or negative scores.

Every reported experiment should record:

- condition and experiment name;
- dataset and sample size;
- model and prompt versions;
- configuration snapshot;
- per-problem outcomes;
- metric definitions and results;
- skipped or failed cases.

The repository currently provides deterministic metric/reporting utilities and
benchmark input structure, but it contains no fabricated benchmark results.
