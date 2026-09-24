# CIPS — Customer Intervention Priority Score

## Purpose and applicability

CIPS turns a fitted-model prediction plus detected business context into a
bounded 0–100 priority ranking. It is applicable or partially applicable for
supervised workflows with a usable risk/probability or predicted-value signal.
It returns `not_applicable` for clustering rather than inventing scores.

CIPS does not assume all datasets contain customer-value, complaint, sentiment,
or engagement variables. It detects optional numeric columns from conservative
name heuristics and records the mapping and any ambiguity warnings.

## Signals and normalization

Potential signals are risk, business value, engagement, complaint/support
activity, sentiment, and recency. Numeric signals use safe min–max
normalization; constant signals become a neutral 0.5. Recency and sentiment are
not automatically inverted because their urgency direction is ambiguous.

For churn/risk targets, CIPS tries to use the semantically likely positive-class
probability. For retention targets it can transparently invert a likely
retained/active-class probability. If this cannot be inferred, CIPS records a
risk-direction warning instead of silently guessing.

## Formula and weights

`CIPS = 100 × Σ(effective_weight_i × normalized_signal_i)`

Base weights are risk 0.45, business value 0.25, engagement 0.10, complaint
0.10, sentiment 0.05, and recency 0.05. Only detected signals participate; the
selected base weights are renormalized to sum to 1.0. Scores are clamped to
0–100 and map to immediate (85+), high (70+), medium (40+), or monitor.

Actions are deterministic generic guidance, not individualized financial or
medical advice. CIPS ranks cases; it does not prove that intervention will
change an outcome.

## AWOF distinction

Prediction answers “What is likely to happen?” Explainability answers “Why did
the model produce this output?” CIPS answers “Which cases should the business
prioritize?” These are separate steps and should not be treated as causal proof.
