import type { ModelTrainingResult, ProblemType } from "../../types/model";

const metric = (value: unknown) => value === null || value === undefined ? "Not available" : String(value);
const modelLabel = (modelId: string) => modelId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function ModelMetrics({ result, problemType }: { result: ModelTrainingResult; problemType: ProblemType }) {
  const metrics = result.test_metrics;
  const labels = problemType === "classification"
    ? [["Accuracy", metrics.accuracy], ["Positive Precision", metrics.positive_precision], ["Positive Recall", metrics.positive_recall], ["Positive F1", metrics.positive_f1], ["ROC-AUC", metrics.roc_auc], ["Brier Score", metrics.brier_score], ["Log Loss", metrics.log_loss], ["Macro F1", metrics.macro_f1], ["Weighted F1", metrics.weighted_f1], ["CV F1", result.cross_validation_metrics.mean]]
    : problemType === "regression"
      ? [["MAE", metrics.mae], ["RMSE", metrics.rmse], ["R²", metrics.r2], ["CV RMSE", result.cross_validation_metrics.mean]]
      : [["Clusters", metrics.cluster_count], ["Silhouette", metrics.silhouette_score], ["Davies-Bouldin", metrics.davies_bouldin_score], ["Calinski-Harabasz", metrics.calinski_harabasz_score], ["Noise %", metrics.noise_percentage]];
  return (
    <article className="card">
      <h3>{modelLabel(result.model_id)}</h3>
      <p>Status: {result.status} · AMRA score: {result.amra_score === undefined ? "Not available" : `${(result.amra_score * 100).toFixed(0)}%`}</p>
      <p>Training time: {result.training_duration_ms} ms</p>
      <table><tbody>{labels.map(([label, value]) => <tr key={String(label)}><th>{String(label)}</th><td>{metric(value)}</td></tr>)}</tbody></table>
      {result.preprocessing_plan && <p className="model-preprocessing"><strong>Leakage-safe preprocessing:</strong> {result.preprocessing_plan.numeric_imputation ?? "no numeric imputation"} imputation, {result.preprocessing_plan.categorical_encoding ?? "no categorical encoding"} encoding{result.preprocessing_plan.scaling ? `, ${result.preprocessing_plan.scaling} scaling` : ""}. {result.preprocessing_plan.outlier_aware_columns.length ? `Robust handling selected for: ${result.preprocessing_plan.outlier_aware_columns.join(", ")}.` : ""}</p>}
      {Array.isArray(metrics.confusion_matrix) && <table><caption>Confusion Matrix</caption><tbody>{(metrics.confusion_matrix as unknown[][]).map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{String(cell)}</td>)}</tr>)}</tbody></table>}
      {result.warnings.length > 0 && <p>{result.warnings.join(" ")}</p>}
    </article>
  );
}
