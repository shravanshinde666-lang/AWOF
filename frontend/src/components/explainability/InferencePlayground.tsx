import { useEffect, useState } from "react";
import { getInferenceSchema, predictLive } from "../../services/explainabilityService";
import type {
  CounterfactualItem,
  InferenceSchemaResponse,
  PredictionResponse,
} from "../../types/explainability";

interface Props {
  datasetId: string;
}

export default function InferencePlayground({ datasetId }: Props) {
  const [schema, setSchema] = useState<InferenceSchemaResponse | null>(null);
  const [inputs, setInputs] = useState<Record<string, string | number | null>>({});
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getInferenceSchema(datasetId)
      .then((loaded) => {
        if (!active) return;
        setSchema(loaded);
        const initial: Record<string, string | number | null> = {};
        for (const feat of loaded.features) {
          initial[feat.name] = feat.default_value;
        }
        if (loaded.sample_rows.length > 0) {
          Object.assign(initial, loaded.sample_rows[0].values);
        }
        setInputs(initial);
        return predictLive(datasetId, initial);
      })
      .then((pred) => {
        if (active && pred) setPrediction(pred);
      })
      .catch(() => {
        if (active) setError("Live inference playground is unavailable for this model.");
      });
    return () => {
      active = false;
    };
  }, [datasetId]);

  async function runPrediction(nextInputs: Record<string, string | number | null>) {
    setLoading(true);
    setError(null);
    try {
      const result = await predictLive(datasetId, nextInputs);
      setPrediction(result);
    } catch {
      setError("Failed to compute live prediction.");
    } finally {
      setLoading(false);
    }
  }

  function handleLoadSample(index: number) {
    if (!schema) return;
    const sample = schema.sample_rows.find((row) => row.row_index === index);
    if (!sample) return;
    const next = { ...inputs, ...sample.values };
    setInputs(next);
    void runPrediction(next);
  }

  function handleApplyCounterfactual(cf: CounterfactualItem) {
    const next = { ...inputs, [cf.feature]: cf.proposed_value };
    setInputs(next);
    void runPrediction(next);
  }

  if (!schema) return null;

  return (
    <section className="card inference-playground" aria-labelledby="playground-heading">
      <div className="section-heading">
        <div>
          <p className="card-kicker">INTERACTIVE SIMULATION</p>
          <h2 id="playground-heading">Live Inference &amp; Counterfactual What-If Playground</h2>
          <p>
            Adjust feature values to simulate real-time model predictions and discover the minimal
            changes needed to shift outcomes.
          </p>
        </div>
        {schema.sample_rows.length > 0 && (
          <label className="select-field" htmlFor="sample-row-preset">
            <span>Load sample record</span>
            <select
              id="sample-row-preset"
              defaultValue="0"
              onChange={(e) => handleLoadSample(Number(e.target.value))}
            >
              {schema.sample_rows.map((sample) => (
                <option key={sample.row_index} value={sample.row_index}>
                  {sample.label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className="evaluation-grid" style={{ marginTop: "1rem" }}>
        <div className="card">
          <h3>Feature Inputs</h3>
          <div style={{ display: "grid", gap: "0.85rem", marginTop: "0.75rem" }}>
            {schema.features.map((feat) => {
              const val = inputs[feat.name] ?? feat.default_value ?? "";
              if (feat.type === "categorical" && feat.categories) {
                return (
                  <label className="select-field" key={feat.name}>
                    <span>{feat.name}</span>
                    <select
                      value={String(val)}
                      onChange={(e) => setInputs({ ...inputs, [feat.name]: e.target.value })}
                    >
                      {feat.categories.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </label>
                );
              }
              return (
                <label className="select-field" key={feat.name}>
                  <span>
                    {feat.name}{" "}
                    {feat.min !== null && feat.max !== null ? (
                      <small style={{ opacity: 0.7 }}>
                        ({feat.min} – {feat.max})
                      </small>
                    ) : null}
                  </span>
                  <input
                    type="number"
                    step={feat.step ?? "any"}
                    value={String(val)}
                    onChange={(e) =>
                      setInputs({
                        ...inputs,
                        [feat.name]: e.target.value === "" ? "" : Number(e.target.value),
                      })
                    }
                  />
                </label>
              );
            })}
          </div>
          <div style={{ marginTop: "1rem" }}>
            <button type="button" onClick={() => void runPrediction(inputs)} disabled={loading}>
              {loading ? "Simulating..." : "Run Live Prediction"}
            </button>
          </div>
        </div>

        <div className="card">
          <h3>Simulated Outcome &amp; Counterfactuals</h3>
          {error && <p className="error-message">{error}</p>}
          {prediction && (
            <div style={{ display: "grid", gap: "1rem", marginTop: "0.75rem" }}>
              <div className="stage-kpis">
                <article>
                  <span>Predicted {schema.target_column ?? "Outcome"}</span>
                  <strong>{prediction.prediction_label}</strong>
                  {prediction.confidence !== null && (
                    <small>{(prediction.confidence * 100).toFixed(1)}% confidence</small>
                  )}
                </article>
              </div>

              {Object.keys(prediction.probabilities).length > 0 && (
                <div>
                  <h4>Class Probabilities</h4>
                  <div style={{ display: "grid", gap: "0.4rem", marginTop: "0.4rem" }}>
                    {Object.entries(prediction.probabilities).map(([cls, prob]) => (
                      <div key={cls} style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Class: <code>{cls}</code></span>
                        <strong>{(prob * 100).toFixed(1)}%</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4>Counterfactual &ldquo;What-If&rdquo; Recommendations</h4>
                {prediction.counterfactuals.length === 0 ? (
                  <p className="empty-state">
                    No single-feature perturbation flipped the outcome within observed bounds.
                  </p>
                ) : (
                  <div style={{ display: "grid", gap: "0.65rem", marginTop: "0.5rem" }}>
                    {prediction.counterfactuals.map((cf) => (
                      <article
                        key={`${cf.feature}-${cf.proposed_value}`}
                        className="card"
                        style={{ padding: "0.75rem" }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
                          <div>
                            <strong>{cf.action_text}</strong>
                            <p style={{ margin: "0.2rem 0 0", fontSize: "0.9rem" }}>
                              {cf.impact} <small>({cf.delta})</small>
                            </p>
                          </div>
                          <button type="button" onClick={() => handleApplyCounterfactual(cf)}>
                            Apply
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
