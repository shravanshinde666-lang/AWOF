# AWOF algorithm overview

AWOF uses a staged, inspectable workflow rather than claiming that one algorithm
fits every tabular dataset.

| Stage | Role | Documentation |
| --- | --- | --- |
| Dataset intelligence | Profiles types, quality, distributions, and correlations | [Dataset Intelligence](dataset_intelligence.md) |
| ACSA | Scores whether capabilities should run, remain optional, or be skipped | [ACSA](acsa.md) |
| AWGA | Builds the validated adaptive workflow graph | [AWGA](awga.md) |
| Pruning | Removes inapplicable workflow nodes with evidence | [Workflow Pruning](workflow_pruning.md) |
| Execution | Applies supported preparation steps on a working copy | [Execution Engine](../architecture/execution_engine.md) |
| AMRA | Ranks suitable candidate models before training | [AMRA](amra.md) |
| Explainability | Produces global/local model explanations with transparent fallbacks | [Explainability](explainability.md) |
| CIPS | Ranks applicable entities for business intervention | [CIPS](cips.md) |
| Research benchmarking | Compares the adaptive workflow with a fixed baseline | [Experiment Design](../research/experiment_design.md) |

Prediction answers **what is likely to happen**. Explainability answers **why a
model produced an output**. CIPS answers **which applicable cases should be
prioritized**. Those are distinct outputs and should not be interpreted as
causal proof or guaranteed business advice.

## Cross-cutting limitations

Feature/target semantics and business-signal detection are heuristic and require
user review. Model metrics are dataset- and split-dependent. Research comparisons
report measured observations, not statistical significance. CIPS does not invent
customer value, complaints, sentiment, or engagement signals when they are not
present. See each linked document for its detailed assumptions and constraints.
