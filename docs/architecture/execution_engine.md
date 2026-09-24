# Execution Engine

ExecutionContext preserves an immutable source DataFrame and a separate working
copy. The module registry maps workflow nodes to reusable preprocessing
functions. The executor follows pruned topological order, records node timing,
row/column changes, artifacts, warnings, and failures.

ML, explainability, and business nodes are preserved as skipped placeholders
until their later phases. Current transforms are demonstration preprocessing;
future model pipelines must fit learned transforms on training data only.
