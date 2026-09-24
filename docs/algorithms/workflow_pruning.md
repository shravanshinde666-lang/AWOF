# Workflow Pruning

Pruning occurs after AWGA and before execution. It inspects the current working
dataset rather than repeating ACSA scoring. Core and configured task nodes are
never pruned. Missing, duplicate, encoding, scaling, selection, outlier, and
PCA nodes are pruned only when their execution-time conditions are absent.

Removed nodes are replaced by direct predecessor-to-successor edges. The
rebuilt graph remains ordered and connected from Dataset Input to Output.
PRUNE-1.0 records every keep/prune decision and reason.
