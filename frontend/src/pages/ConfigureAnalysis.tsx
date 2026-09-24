import { AxiosError } from "axios";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ConfigurationSummary from "../components/configuration/ConfigurationSummary";
import Loading from "../components/common/Loading";
import {
  getBusinessObjectives,
  getTargetCandidates,
  saveConfiguration,
} from "../services/configurationService";
import type {
  AnalysisConfiguration,
  BusinessObjective,
  TargetCandidate,
} from "../types/configuration";

function errorMessage(cause: unknown): string {
  if (cause instanceof AxiosError) {
    const body = cause.response?.data as { error?: string; details?: string[] } | undefined;
    return body?.details?.join(" ") ?? body?.error ?? "Unable to save the configuration.";
  }
  return "Unable to load or save the configuration.";
}

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/w/g, (letter) => letter.toUpperCase());
}

export default function ConfigureAnalysis() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [objectives, setObjectives] = useState<BusinessObjective[]>([]);
  const [candidates, setCandidates] = useState<TargetCandidate[]>([]);
  const [objectiveId, setObjectiveId] = useState("");
  const [targetColumn, setTargetColumn] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [configuration, setConfiguration] = useState<AnalysisConfiguration | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    Promise.all([getBusinessObjectives(), getTargetCandidates(datasetId)])
      .then(([loadedObjectives, loadedCandidates]) => {
        setObjectives(loadedObjectives);
        setCandidates(loadedCandidates);
      })
      .catch((cause) => setError(errorMessage(cause)))
      .finally(() => setLoading(false));
  }, [datasetId]);

  const objective = useMemo(
    () => objectives.find((item) => item.id === objectiveId),
    [objectiveId, objectives],
  );
  const selectedTarget = candidates.find((item) => item.column === targetColumn);
  const targetRequired = objective?.target_requirement === "required";
  const canSave = Boolean(objective && (!targetRequired || targetColumn) && !saving);

  const save = async () => {
    if (!datasetId || !objective) return;
    setSaving(true);
    setError(null);
    try {
      setConfiguration(await saveConfiguration(datasetId, {
        business_objective: objective.id,
        target_column: objective.target_requirement === "none" ? null : targetColumn || null,
      }));
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <main className="page"><Loading message="Loading analysis configuration..." /></main>;

  return (
    <main className="page configuration-page">
      <Link className="back-link" to={datasetId ? `/datasets/${datasetId}/intelligence` : "/upload"}>← Dataset Intelligence</Link>
      <p className="eyebrow">AWOF</p>
      <h1>Configure Analysis</h1>
      <p>Choose a business objective first. AWOF then suggests a technical problem type based on your target choice.</p>
      {error && <p className="error-message" role="alert">{error}</p>}

      <section>
        <h2>Choose Business Objective</h2>
        <div className="objective-grid">
          {objectives.map((item) => (
            <button type="button" key={item.id} className={objectiveId === item.id ? "objective-card selected" : "objective-card"} onClick={() => { setObjectiveId(item.id); setTargetColumn(""); setConfiguration(null); }}>
              <strong>{item.label}</strong><span>{item.description}</span><small>Target: {item.target_requirement}</small>
            </button>
          ))}
        </div>
      </section>

      {objective && (
        <section className="configuration-panel">
          <h2>Select Target Column</h2>
          {objective.target_requirement === "none" ? (
            <p>Target column is not required for customer segmentation. Technical problem: <strong>Clustering</strong>.</p>
          ) : (
            <>
              <p>{objective.target_requirement === "optional"
                ? "A numerical target can be selected for prediction, or you may continue with business analysis."
                : "A target column is required for this objective."}</p>
              <label className="select-field" htmlFor="target-column">
                <span>Target column</span>
                <select id="target-column" value={targetColumn} onChange={(event) => setTargetColumn(event.target.value)}>
                  <option value="">{objective.target_requirement === "optional" ? "No target selected" : "Select a target"}</option>
                  {candidates.map((candidate) => <option key={candidate.column} value={candidate.column}>{candidate.column} — {candidate.target_suitability}</option>)}
                </select>
              </label>
              {selectedTarget && <article className="target-details">
                <h3>{selectedTarget.column}</h3>
                <p>{humanize(selectedTarget.detected_type)} · {selectedTarget.unique_count} unique values · {selectedTarget.missing_percentage.toFixed(2)}% missing</p>
                <p>Suitability: <strong>{humanize(selectedTarget.target_suitability)}</strong></p>
                <p>Suggested task: <strong>{humanize(selectedTarget.suggested_problem_type)}</strong></p>
                {selectedTarget.reasons.map((reason) => <p key={reason}>{reason}</p>)}
                {selectedTarget.warnings.map((warning) => <p className="configuration-warning" key={warning}>Warning: {warning}</p>)}
              </article>}
            </>
          )}
          <section className="confirmation-box">
            <h3>Analysis Configuration</h3>
            <p>Objective: {objective.label}</p>
            <p>Target: {objective.target_requirement === "none" ? "Not required" : targetColumn || "Not selected"}</p>
            <p>Technical problem: {objective.target_requirement === "none" ? "Clustering" : selectedTarget ? humanize(selectedTarget.suggested_problem_type) : objective.target_requirement === "optional" && !targetColumn ? "Business Analysis" : "Pending target selection"}</p>
          </section>
          <button type="button" onClick={() => void save()} disabled={!canSave}>{saving ? "Saving configuration..." : "Save Configuration"}</button>
        </section>
      )}
      {configuration && <ConfigurationSummary configuration={configuration} />}
    </main>
  );
}
