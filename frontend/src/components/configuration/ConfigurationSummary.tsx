import type { AnalysisConfiguration } from "../../types/configuration";
import { useNavigate } from "react-router-dom";

export default function ConfigurationSummary({ configuration }: { configuration: AnalysisConfiguration }) {
  const navigate = useNavigate();
  return (
    <section className="configuration-summary">
      <h2>Configuration Saved</h2>
      <p>Dataset is ready for adaptive capability analysis.</p>
      <dl>
        <dt>Business Objective</dt><dd>{configuration.business_objective.label}</dd>
        <dt>Target</dt><dd>{configuration.target?.column ?? "Not required"}</dd>
        <dt>Technical Problem</dt><dd>{configuration.problem_type.replaceAll("_", " ")}</dd>
        <dt>Status</dt><dd>{configuration.valid ? "Ready" : "Needs review"}</dd>
      </dl>
      {configuration.warnings.map((warning) => <p className="configuration-warning" key={warning}>Warning: {warning}</p>)}
      <button type="button" onClick={() => navigate(`/datasets/${configuration.dataset_id}/capabilities`)}>Run Capability Analysis</button>
    </section>
  );
}
