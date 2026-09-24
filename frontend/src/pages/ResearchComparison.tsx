import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getDatasetExperiments,
  getExperiment,
  runComparison,
} from "../services/experimentService";
import type {
  ExperimentSummary,
  MeasuredValue,
  PipelineExperimentResult,
  ResearchExperimentResult,
} from "../types/experiment";

const PERFORMANCE_KEYS = {
  classification: ["f1", "accuracy", "precision", "recall", "roc_auc"],
  regression: ["rmse", "mae", "r2"],
  clustering: ["silhouette_score", "davies_bouldin_score", "calinski_harabasz_score"],
} as const;

function measuredMean(value: MeasuredValue | undefined): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  return value && Number.isFinite(value.mean) ? value.mean : null;
}

function measuredDeviation(value: MeasuredValue | undefined): number | null {
  if (typeof value === "number") return null;
  return value && Number.isFinite(value.std) ? value.std : null;
}

function includeRunStatistic(
  value: MeasuredValue | undefined,
  statistic: { mean: number; std: number } | undefined,
): MeasuredValue | undefined {
  return statistic ?? value;
}

function formatNumber(value: number | null | undefined, digits = 3): string {
  return value === null || value === undefined || !Number.isFinite(value)
    ? "N/A"
    : value.toFixed(digits);
}

function formatMeasured(value: MeasuredValue | undefined, unit: string): string {
  const mean = measuredMean(value);
  const deviation = measuredDeviation(value);
  if (mean === null) return "N/A";
  const formattedMean = `${formatNumber(mean, 2)} ${unit}`;
  return deviation === null ? formattedMean : `${formattedMean} +/- ${formatNumber(deviation, 2)} ${unit}`;
}

function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "N/A" : `${formatNumber(value, 1)}%`;
}

function modelNames(pipeline: PipelineExperimentResult): string {
  return pipeline.models.trained_ids?.length
    ? pipeline.models.trained_ids.join(", ")
    : "No successfully trained models reported";
}

function bestModelName(pipeline: PipelineExperimentResult): string {
  const best = pipeline.best_model;
  return best ? (best.label ?? best.model_id) : "N/A";
}

function ComparisonBar({
  label,
  baseline,
  awof,
  unit,
}: {
  label: string;
  baseline: MeasuredValue | undefined;
  awof: MeasuredValue | undefined;
  unit: string;
}) {
  const baselineValue = measuredMean(baseline);
  const awofValue = measuredMean(awof);
  const maximum = Math.max(baselineValue ?? 0, awofValue ?? 0, 1);
  const width = (value: number | null) => value === null ? "0%" : `${(value / maximum) * 100}%`;

  return (
    <section className="card">
      <h3>{label}</h3>
      <div className="importance-row">
        <span>Fixed</span>
        <div className="importance-track"><span style={{ width: width(baselineValue) }} /></div>
        <small>{formatMeasured(baseline, unit)}</small>
      </div>
      <div className="importance-row">
        <span>AWOF</span>
        <div className="importance-track"><span style={{ width: width(awofValue) }} /></div>
        <small>{formatMeasured(awof, unit)}</small>
      </div>
    </section>
  );
}

function CountComparisonBar({
  label,
  baseline,
  awof,
}: {
  label: string;
  baseline: number;
  awof: number;
}) {
  const maximum = Math.max(baseline, awof, 1);
  return (
    <section className="card">
      <h3>{label}</h3>
      <div className="importance-row">
        <span>Fixed</span>
        <div className="importance-track"><span style={{ width: `${(baseline / maximum) * 100}%` }} /></div>
        <small>{baseline}</small>
      </div>
      <div className="importance-row">
        <span>AWOF</span>
        <div className="importance-track"><span style={{ width: `${(awof / maximum) * 100}%` }} /></div>
        <small>{awof}</small>
      </div>
    </section>
  );
}

function ResultView({ result }: { result: ResearchExperimentResult }) {
  const { baseline, awof, comparison } = result;
  const metricKeys = PERFORMANCE_KEYS[result.problem_type];

  return (
    <>
      <section className="card">
        <h2>Experiment Result</h2>
        <p>
          Dataset: {result.dataset_name} - Problem Type: {result.problem_type} - Benchmark runs: {result.metadata.runs}
        </p>
        <p>
          Objective: {result.objective}{result.target ? ` - Target: ${result.target}` : ""}
        </p>
        <p>Experiment ID: {result.experiment_id}</p>
      </section>

      <section className="card">
        <h2>Fixed Pipeline vs AWOF</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr><th>Metric</th><th>Fixed Pipeline</th><th>AWOF</th></tr>
            </thead>
            <tbody>
              <tr><th>Modules Executed</th><td>{baseline.workflow_modules.executed}</td><td>{awof.workflow_modules.executed}</td></tr>
              <tr><th>Models Trained</th><td>{baseline.models.trained}</td><td>{awof.models.trained}</td></tr>
              <tr><th>Execution Time</th><td>{formatMeasured(includeRunStatistic(baseline.timings_ms.overall, baseline.run_statistics?.timings_ms?.overall), "ms")}</td><td>{formatMeasured(includeRunStatistic(awof.timings_ms.overall, awof.run_statistics?.timings_ms?.overall), "ms")}</td></tr>
              <tr><th>Peak Python Memory</th><td>{formatMeasured(includeRunStatistic(baseline.resources.peak_python_memory_mb, baseline.run_statistics?.resources?.peak_python_memory_mb), "MB")}</td><td>{formatMeasured(includeRunStatistic(awof.resources.peak_python_memory_mb, awof.run_statistics?.resources?.peak_python_memory_mb), "MB")}</td></tr>
              <tr><th>Primary Performance ({comparison.performance.metric})</th><td>{formatNumber(comparison.performance.baseline)}</td><td>{formatNumber(comparison.performance.awof)}</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h2>Efficiency Indicators</h2>
        <div className="summary-grid">
          <article className="summary-card"><strong>Modules Avoided</strong><span>{comparison.module_reduction_count} ({formatPercent(comparison.module_reduction_percentage)})</span></article>
          <article className="summary-card"><strong>Models Avoided</strong><span>{comparison.model_reduction_count} ({formatPercent(comparison.model_reduction_percentage)})</span></article>
          <article className="summary-card"><strong>Time Difference</strong><span>{formatNumber(comparison.execution_time_difference_ms, 2)} ms ({formatPercent(comparison.execution_time_reduction_percentage)})</span></article>
          <article className="summary-card"><strong>Memory Difference</strong><span>{formatNumber(comparison.memory_difference_mb, 2)} MB ({formatPercent(comparison.memory_reduction_percentage)})</span></article>
          <article className="summary-card"><strong>Performance Difference</strong><span>{formatNumber(comparison.performance.difference)} ({comparison.performance.direction})</span></article>
        </div>
      </section>

      <section className="card">
        <h2>Workflow Modules</h2>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Measure</th><th>Fixed Pipeline</th><th>AWOF</th></tr></thead>
            <tbody>
              <tr><th>Considered</th><td>{baseline.workflow_modules.considered}</td><td>{awof.workflow_modules.considered}</td></tr>
              <tr><th>Selected</th><td>{baseline.workflow_modules.selected ?? "N/A"}</td><td>{awof.workflow_modules.selected ?? "N/A"}</td></tr>
              <tr><th>Pruned</th><td>{baseline.workflow_modules.pruned ?? "N/A"}</td><td>{awof.workflow_modules.pruned ?? "N/A"}</td></tr>
              <tr><th>Executed</th><td>{baseline.workflow_modules.executed}</td><td>{awof.workflow_modules.executed}</td></tr>
            </tbody>
          </table>
        </div>
        {awof.workflow_modules.ids?.length ? <p>AWOF executed: {awof.workflow_modules.ids.join(", ")}</p> : null}
      </section>

      <section className="card">
        <h2>Models</h2>
        <p><strong>Fixed trained:</strong> {modelNames(baseline)}</p>
        <p><strong>AWOF trained:</strong> {modelNames(awof)}</p>
        <p><strong>Fixed best model:</strong> {bestModelName(baseline)}</p>
        <p><strong>AWOF best model:</strong> {bestModelName(awof)}</p>
      </section>

      <section className="card">
        <h2>Performance Details</h2>
        <div className="table-scroll">
          <table>
            <thead><tr><th>Metric</th><th>Fixed Pipeline</th><th>AWOF</th></tr></thead>
            <tbody>
              {metricKeys.map((metric) => (
                <tr key={metric}>
                  <th>{metric.replaceAll("_", " ")}</th>
                  <td>{formatNumber(baseline.best_metrics[metric])}</td>
                  <td>{formatNumber(awof.best_metrics[metric])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <h2>Measured Comparisons</h2>
      <ComparisonBar label="Mean Runtime" baseline={includeRunStatistic(baseline.timings_ms.overall, baseline.run_statistics?.timings_ms?.overall)} awof={includeRunStatistic(awof.timings_ms.overall, awof.run_statistics?.timings_ms?.overall)} unit="ms" />
      <ComparisonBar label="Mean Peak Python Memory" baseline={includeRunStatistic(baseline.resources.peak_python_memory_mb, baseline.run_statistics?.resources?.peak_python_memory_mb)} awof={includeRunStatistic(awof.resources.peak_python_memory_mb, awof.run_statistics?.resources?.peak_python_memory_mb)} unit="MB" />
      <CountComparisonBar label="Models Trained" baseline={baseline.models.trained} awof={awof.models.trained} />
      <CountComparisonBar label="Modules Executed" baseline={baseline.workflow_modules.executed} awof={awof.workflow_modules.executed} />

      <section className="card">
        <h2>Research Interpretation</h2>
        {comparison.factual_statements.length ? (
          <ul>{comparison.factual_statements.map((statement) => <li key={statement}>{statement}</li>)}</ul>
        ) : <p>No interpretation was generated; the measured values above are shown directly.</p>}
        <p>These observations describe this experiment only. They do not establish statistical significance.</p>
      </section>

      {result.warnings.length > 0 && (
        <section className="card">
          <h2>Experiment Warnings</h2>
          <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
        </section>
      )}
    </>
  );
}

export default function ResearchComparison() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [runs, setRuns] = useState("3");
  const [experimentName, setExperimentName] = useState("");
  const [history, setHistory] = useState<ExperimentSummary[]>([]);
  const [result, setResult] = useState<ResearchExperimentResult | null>(null);
  const [selectedExperimentId, setSelectedExperimentId] = useState("");
  const [running, setRunning] = useState(false);
  const [loadingResult, setLoadingResult] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    const id = datasetId;
    let active = true;

    async function loadHistory() {
      try {
        const experiments = await getDatasetExperiments(id);
        if (!active) return;
        setHistory(experiments);
        const latest = experiments[0];
        if (!latest) return;
        setSelectedExperimentId(latest.experiment_id);
        setLoadingResult(true);
        const latestResult = await getExperiment(latest.experiment_id);
        if (active) setResult(latestResult);
      } catch {
        if (active) setError("Previous research experiments could not be loaded. You can run a new comparison.");
      } finally {
        if (active) setLoadingResult(false);
      }
    }

    void loadHistory();
    return () => { active = false; };
  }, [datasetId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!datasetId) return;
    const runCount = Number(runs);
    if (!Number.isInteger(runCount) || runCount < 1 || runCount > 10) {
      setError("Benchmark runs must be a whole number from 1 to 10.");
      return;
    }

    setRunning(true);
    setError(null);
    try {
      const generated = await runComparison(datasetId, runCount, experimentName);
      setResult(generated);
      setSelectedExperimentId(generated.experiment_id);
      const refreshedHistory = await getDatasetExperiments(datasetId);
      setHistory(refreshedHistory);
    } catch {
      setError("The research comparison could not be completed. Confirm that the dataset has been profiled and configured, then try again.");
    } finally {
      setRunning(false);
    }
  }

  async function selectExperiment(experimentId: string) {
    setSelectedExperimentId(experimentId);
    if (!experimentId) return;
    setLoadingResult(true);
    setError(null);
    try {
      setResult(await getExperiment(experimentId));
    } catch {
      setError("The selected research experiment could not be retrieved.");
    } finally {
      setLoadingResult(false);
    }
  }

  return (
    <main className="page">
      <Link className="back-link" to={`/datasets/${datasetId}/business`}>Back to business intelligence</Link>
      <h1>Research Comparison</h1>
      <p>Compare a fixed, conventional pipeline with AWOF using the same configured dataset and deterministic split policy.</p>

      <section className="card">
        <h2>Run Fixed vs AWOF Experiment</h2>
        <form onSubmit={submit}>
          <label className="select-field">
            Benchmark Runs
            <input type="number" min="1" max="10" step="1" value={runs} onChange={(event) => setRuns(event.target.value)} disabled={running} />
          </label>
          <label className="select-field">
            Experiment Name (optional)
            <input type="text" value={experimentName} onChange={(event) => setExperimentName(event.target.value)} disabled={running} />
          </label>
          <p>Multiple benchmark runs may take longer because fresh models are retrained for each run.</p>
          <button type="submit" disabled={running}>{running ? "Running research experiment..." : "Run Fixed vs AWOF Experiment"}</button>
        </form>
      </section>

      {history.length > 0 && (
        <section className="card">
          <h2>Saved Experiments</h2>
          <label className="select-field">
            Load a result
            <select value={selectedExperimentId} onChange={(event) => void selectExperiment(event.target.value)} disabled={running || loadingResult}>
              {history.map((experiment) => <option value={experiment.experiment_id} key={experiment.experiment_id}>{experiment.dataset_name} - {experiment.problem_type} - {experiment.timestamp}</option>)}
            </select>
          </label>
        </section>
      )}

      {error && <p className="error-message">{error}</p>}
      {loadingResult && <p>Loading research experiment...</p>}
      {result && !loadingResult && <ResultView result={result} />}
    </main>
  );
}
