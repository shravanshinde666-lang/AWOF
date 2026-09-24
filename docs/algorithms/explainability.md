# Explainability Engine

## Supported models and methods

The engine loads the serialized complete fitted scikit-learn pipeline rather
than retraining it. It supports the Phase 6 linear, random forest, and gradient
boosting classifiers and regressors. Clustering is interpreted through feature
centroid/profile differences rather than forced into a supervised explanation.

SHAP is optional and is not installed in this environment. AWOF therefore
reports its actual deterministic fallback method:

- tree models: `native_feature_importance` globally and a clearly labelled
  `native_importance_proxy` locally;
- linear models: `linear_coefficients`;
- other supported estimators: `permutation_importance` when a target is
  available.

No fallback result is labelled as SHAP.

## Global and local results

Global importance returns the top 20 ranked features, magnitude, optional
direction, and recoverable original feature. Local requests are bounded to ten
factors and return one row's prediction, available class probabilities or
predicted regression value, baseline where meaningful, contributions, and
positive/negative factors. Classification probabilities are returned by class;
their business risk meaning is left to CIPS semantic handling.

## Feature names and limitations

The engine calls the fitted `ColumnTransformer.get_feature_names_out()` so
one-hot encoded names remain understandable, such as `Contract_Month-to-month`,
instead of anonymous `x0` values. Native tree local factors are an
input-weighted importance proxy, not causal or SHAP-attribution values; the API
warns about that distinction. Explainability describes model behavior and does
not establish causation.
