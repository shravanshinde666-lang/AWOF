import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getDataset,
  getDatasetHistory,
  type DatasetHistoryResponse,
  type DatasetMetadata,
} from "../services/datasetService";

const stageLabels: Record<string, string> = {
  profile: "Dataset Intelligence",
  configuration: "Analysis Configuration",
  capabilities: "ACSA Capability Decisions",
  workflow: "AWGA Workflow",
  pruned_workflow: "Optimized Workflow",
  execution: "Execution",
  model_recommendations: "AMRA Recommendations",
  model_evaluation: "Model Evaluation",
  explainability: "Explainability",
  business_priority: "CIPS Priorities",
};

const stageRoutes: Record<string, string> = {
  profile: "intelligence",
  configuration: "configure",
  capabilities: "capabilities",
  workflow: "workflow",
  pruned_workflow: "workflow",
  execution: "execution",
  model_recommendations: "models",
  model_evaluation: "evaluation",
  explainability: "explainability",
  business_priority: "business",
};

export default function ProjectHistory() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [dataset, setDataset] = useState<DatasetMetadata | null>(null);
  const [history, setHistory] = useState<DatasetHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    Promise.all([getDataset(datasetId), getDatasetHistory(datasetId)])
      .then(([metadata, result]) => { setDataset(metadata); setHistory(result); })
      .catch(cause => setError(cause instanceof Error ? cause.message : "Project history could not be loaded."));
  }, [datasetId]);

  if (error) return <main className="page"><p className="error-message" role="alert">{error}</p></main>;
  if (!dataset || !history) return <main className="page route-loading" role="status">Loading project history...</main>;

  return <main className="page history-page">
    <header className="page-hero">
      <p className="eyebrow">PROJECT AUDIT TRAIL</p>
      <h1>Project History</h1>
      <p>{dataset.original_filename} · {dataset.rows.toLocaleString()} rows · {dataset.columns} columns</p>
    </header>
    <section className="stage-kpis">
      <article><span>Completed stages</span><strong>{history.stages.length}</strong><small>Persisted results</small></article>
      <article><span>Dataset type</span><strong>{dataset.file_type.toUpperCase()}</strong><small>Uploaded source</small></article>
      <article><span>Latest activity</span><strong>{history.stages.length ? new Date(history.stages.at(-1)!.updated_at).toLocaleDateString() : "No activity"}</strong><small>Last persisted stage</small></article>
    </section>
    <section className="dashboard-card">
      <div className="section-heading"><div><p className="eyebrow">PERSISTED EVENTS</p><h2>Analysis timeline</h2></div><Link to={`/datasets/${datasetId}/report`}>Open final report →</Link></div>
      {history.stages.length ? <ol className="history-timeline">
        {history.stages.map((item, index) => {
          const destination = stageRoutes[item.stage];
          const content = <><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{stageLabels[item.stage] ?? item.stage.replaceAll("_", " ")}</strong><small>{new Date(item.updated_at).toLocaleString()}</small></div></>;
          return <li key={`${item.stage}-${item.updated_at}`}>{destination ? <Link to={`/datasets/${datasetId}/${destination}`}>{content}</Link> : content}</li>;
        })}
      </ol> : <p className="empty-state">No analysis stages have been persisted yet.</p>}
    </section>
  </main>;
}
