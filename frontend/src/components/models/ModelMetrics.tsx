import type { ModelTrainingResult, ProblemType } from "../../types/model";

const metric = (value: unknown) => value === null || value === undefined ? "Not available" : String(value);

export default function ModelMetrics({ result, problemType }: { result: ModelTrainingResult; problemType: ProblemType }) {
  const metrics = result.test_metrics;
  const labels = problemType === "classification"
    ? [["Accuracy", metrics.accuracy], ["Precision", metrics.precision], ["Recall", metrics.recall], ["F1", metrics.f1], ["ROC-AUC", metrics.roc_auc], ["CV F1", result.cross_validation_metrics.mean]]
    : problemType === "regression"
      ? [["MAE", metrics.mae], ["RMSE", metrics.rmse], ["R²", metrics.r2], ["CV RMSE", result.cross_validation_metrics.mean]]
      : [["Clusters", metrics.cluster_count], ["Silhouette", metrics.silhouette_score], ["Davies-Bouldin", metrics.davies_bouldin_score], ["Calinski-Harabasz", metrics.calinski_harabasz_score], ["Noise %", metrics.noise_percentage]];
  return (
    <article className="card">
      <h3>{result.model_id}</h3>
      <p>Status: {result.status} · AMRA score: {result.amra_score === undefined ? "Not available" : `${(result.amra_score * 100).toFixed(0)}%`}</p>
      <p>Training time: {result.training_duration_ms} ms</p>
      <table><tbody>{labels.map(([label, value]) => <tr key={String(label)}><th>{String(label)}</th><td>{metric(value)}</td></tr>)}</tbody></table>
      {Array.isArray(metrics.confusion_matrix) && <table><caption>Confusion Matrix</caption><tbody>{(metrics.confusion_matrix as unknown[][]).map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{String(cell)}</td>)}</tr>)}</tbody></table>}
      {result.warnings.length > 0 && <p>{result.warnings.join(" ")}</p>}
    </article>
  );
}
