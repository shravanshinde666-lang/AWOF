import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getDatasetSummary,
  getFinalReport,
  listDatasets,
  type DatasetSummaryResponse,
  type FinalReportResponse,
} from "../services/datasetService";

type AnyMap = Record<string, any>;

const workflowStages = [
  ["Intelligence", "profile"], ["Configure", "configuration"],
  ["ACSA", "capabilities"], ["Workflow", "workflow"],
  ["Execute", "execution"], ["AMRA", "model_recommendations"],
  ["Evaluation", "model_evaluation"], ["Explain", "explainability"],
  ["Priorities", "business_priority"],
] as const;

export default function Home() {
  const [projects, setProjects] = useState<DatasetSummaryResponse[]>([]);
  const [report, setReport] = useState<FinalReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadOverview() {
      try {
        const datasets = await listDatasets();
        const summaries = await Promise.allSettled(
          datasets.slice(0, 6).map(item => getDatasetSummary(item.dataset_id)),
        );
        const available = summaries
          .filter((item): item is PromiseFulfilledResult<DatasetSummaryResponse> => item.status === "fulfilled")
          .map(item => item.value);
        if (cancelled) return;
        setProjects(available);
        if (available[0]) {
          const compactReport = await getFinalReport(available[0].dataset.dataset_id, true);
          if (!cancelled) setReport(compactReport);
        }
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "The project overview could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadOverview();
    return () => { cancelled = true; };
  }, []);

  const current = projects[0];
  const completedStages = useMemo(
    () => new Set(current?.stages.map(item => item.stage) ?? []),
    [current],
  );
  const data = (report?.stages ?? {}) as AnyMap;
  const profileSummary = data.profile?.summary;
  const config = data.configuration?.configuration ?? data.configuration;
  const acsa = data.capabilities;
  const evaluation = data.model_evaluation;
  const explainability = data.explainability;
  const cipsSummary = data.business_priority?.summary;
  const missingPercentage = typeof profileSummary?.missing_percentage === "number"
    ? `${profileSummary.missing_percentage.toFixed(3)}%`
    : null;

  if (loading) return <main className="home-page route-loading" role="status">Loading project overview...</main>;

  return <main className="home-page overview-page">
    <header className="overview-header"><div><p className="eyebrow">ADAPTIVE ANALYTICS WORKSPACE</p><h1>Project Overview</h1><p>Actual persisted results from the latest analysis.</p></div><Link className="primary-link" to="/upload">+ New analysis</Link></header>
    {error && <p className="error-message" role="alert">{error}</p>}
    {current ? <>
      <section className="stage-kpis">
        <article><span>Rows</span><strong>{current.dataset.rows.toLocaleString()}</strong></article>
        <article><span>Columns</span><strong>{current.dataset.columns}</strong></article>
        <article><span>Target</span><strong>{config?.target?.column ?? "Not configured"}</strong></article>
        <article><span>Problem type</span><strong>{config?.problem_type ?? "Pending"}</strong></article>
        <article><span>Missing</span><strong>{profileSummary ? `${profileSummary.missing_cells ?? 0}${missingPercentage ? ` (${missingPercentage})` : ""}` : "Pending"}</strong></article>
        <article><span>Duplicates</span><strong>{profileSummary?.duplicate_rows ?? "Pending"}</strong></article>
      </section>
      <section className="dashboard-card"><div className="section-heading"><div><p className="eyebrow">CURRENT ADAPTIVE WORKFLOW</p><h2>{current.dataset.original_filename}</h2></div><div className="overview-links"><Link to={`/datasets/${current.dataset.dataset_id}/history`}>View history</Link><Link to={`/datasets/${current.dataset.dataset_id}/intelligence`}>Open project →</Link></div></div><div className="overview-stage-grid">{workflowStages.map(([label, key]) => <article className={completedStages.has(key) ? "complete" : "pending"} key={key}><span>{completedStages.has(key) ? "✓" : "○"}</span><strong>{label}</strong><small>{completedStages.has(key) ? "Available" : "Not run"}</small></article>)}</div></section>
      <section className="dashboard-grid dashboard-grid-primary overview-insights">
        <article className="dashboard-card"><span className="card-kicker">ACSA</span><h3>Capability decisions</h3>{acsa?.summary ? <p><strong>{acsa.summary.run_count}</strong> run · {acsa.summary.optional_count} optional · {acsa.summary.skip_count} skip</p> : <p className="empty-state">Capability analysis not run.</p>}</article>
        <article className="dashboard-card"><span className="card-kicker">BEST MODEL</span><h3>{evaluation?.best_model?.model_id?.replaceAll("_", " ") ?? "No evaluation yet"}</h3>{evaluation?.best_model && <p>{evaluation.best_model.why_selected}</p>}</article>
        <article className="dashboard-card"><span className="card-kicker">EXPLAINABILITY</span><h3>{explainability?.explanation_method?.replaceAll("_", " ") ?? "Not generated"}</h3><p>{explainability?.global_importance?.[0]?.feature ? `Top feature: ${explainability.global_importance[0].feature}` : "Complete model evaluation first."}</p></article>
        <article className="dashboard-card"><span className="card-kicker">CIPS</span><h3>{cipsSummary ? `${cipsSummary.immediate_count} immediate priorities` : "Not generated"}</h3><p>{cipsSummary ? `${cipsSummary.entities_scored} entities scored` : "Business priorities appear when applicable."}</p></article>
        <article className="dashboard-card"><span className="card-kicker">RESEARCH</span><h3>{report?.research ? "Comparison available" : "Not run"}</h3><p>Fixed pipeline versus adaptive AWOF evidence.</p></article>
      </section>
    </> : <section className="hero-panel"><div className="hero-copy"><p className="eyebrow">NO PROJECT YET</p><h1>Make every workflow <em>fit the data.</em></h1><p className="subtitle">Upload a CSV or Excel dataset to begin.</p><Link className="primary-link" to="/upload">Start new analysis</Link></div></section>}
    <section className="project-list"><h2>Recent projects</h2>{projects.map(project => <Link className="project-row" to={`/datasets/${project.dataset.dataset_id}/intelligence`} key={project.dataset.dataset_id}><span><strong>{project.dataset.original_filename}</strong><small>{project.dataset.rows.toLocaleString()} rows · {project.dataset.columns} columns</small></span><b>{project.stages.length} stages</b></Link>)}</section>
  </main>;
}
