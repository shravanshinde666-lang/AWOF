# Adaptive Workflow Generation Algorithm

AWGA-1.0 consumes a dataset profile, valid configuration, and ACSA result. It
creates core Dataset Input, Dataset Profile, and Output nodes, maps selected
capabilities to workflow nodes, emits explicit edges, validates a DAG, and
returns deterministic topological order.

RUN capabilities are included and SKIP capabilities are retained as excluded
metadata. OPTIONAL nodes are included only when deterministic rules justify
them: scaling for clustering, encoding for task-relevant categorical features,
feature selection for width/identifier/constant signals, explainability for
supervised tasks, and dimensionality reduction for clustering or high numeric
width.

Nodes follow fixed stage ordering. Each included adaptive node depends on the
prior included stage, so edges are directed and dependencies precede targets.
Validation checks core nodes, edge validity, cycle absence, and task
exclusivity. A topological sort supplies future execution order.

## Why AWGA is not a fixed pipeline

A fixed pipeline runs a predefined sequence. AWGA constructs structure from
dataset characteristics, business objective, problem type, ACSA scores, and
dependency constraints. Different inputs can therefore produce different DAGs.
AWGA only generates the graph; it performs no transformations or ML execution.
