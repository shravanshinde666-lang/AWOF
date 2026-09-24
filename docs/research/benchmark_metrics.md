# Phase 8 benchmark metrics

## Measurement conventions

All elapsed-time values are wall-clock milliseconds measured with
`time.perf_counter`. Peak memory is a clearly labelled Python-allocation
measurement in MiB, measured by `tracemalloc`; it is not total machine RAM.
CPU process time is supplementary when available.

Let `B` be the fixed baseline value and `A` be the AWOF value. Percentage
metrics are `null` with a warning when their denominator is zero; they are not
silently reported as `0%`.

## Operational efficiency metrics

| Metric | Formula | Interpretation |
| --- | --- | --- |
| Modules avoided | `B_modules - A_modules` | Positive means AWOF executed fewer named modules. |
| Module reduction % | `100 * (B_modules - A_modules) / B_modules` | `null` if `B_modules = 0`. |
| Models avoided | `B_models_trained - A_models_trained` | Positive means AWOF trained fewer models. |
| Model reduction % | `100 * (B_models_trained - A_models_trained) / B_models_trained` | `null` if no baseline models trained. |
| Time difference | `B_time_ms - A_time_ms` | Positive means AWOF had lower wall-clock time. |
| Time reduction % | `100 * (B_time_ms - A_time_ms) / B_time_ms` | `null` if baseline time is zero. |
| Memory difference | `B_peak_memory_mb - A_peak_memory_mb` | Positive means AWOF used less measured Python allocation memory. |
| Memory reduction % | `100 * (B_memory_mb - A_memory_mb) / B_memory_mb` | `null` if baseline memory is zero. |

Module counts include only meaningful named operations that were applicable and
executed. The fixed path does not get artificial counts for impossible tasks,
and the adaptive path records AWGA-included, pruned, and actually executed
modules separately.

## Performance metrics

| Problem type | Primary metric | Performance difference | Direction |
| --- | --- | --- | --- |
| Classification | F1 | `A_f1 - B_f1` | Positive favours AWOF. |
| Regression | RMSE | `A_rmse - B_rmse` | Negative favours AWOF because lower is better. |
| Clustering | Silhouette score | `A_silhouette - B_silhouette` | Positive favours AWOF. |

Classification results also retain accuracy, precision, recall, and ROC-AUC
when valid. Regression retains MAE, RMSE, and R2. Clustering retains silhouette
score, Davies-Bouldin, and Calinski-Harabasz where the data and labels make the
metric valid.

## Repeated-run statistics

For each runner the experiment stores every run and calculates arithmetic mean
and sample standard deviation for overall runtime and peak memory. These values
describe observed variability only; the engine does not make automatic
statistical-significance claims.

## Reading the results

Positive reductions show lower AWOF operational cost, but are not proof of
superiority. Performance comparisons must be read with their problem-specific
direction. A configured tolerance, if shown, is a project reporting convention
and not a universal scientific threshold.
