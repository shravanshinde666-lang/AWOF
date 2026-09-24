import type { LocalExplanation } from "../../types/explainability";

function Factors({ title, factors }: { title: string; factors: LocalExplanation["feature_contributions"] }) {
  return <section><h3>{title}</h3>{factors.length === 0 ? <p>None identified.</p> : <ul>{factors.map((factor) => <li key={factor.feature}>{factor.feature}: {factor.contribution.toFixed(4)}</li>)}</ul>}</section>;
}

export default function ShapChart({ explanation }: { explanation: LocalExplanation }) {
  return <section className="card"><h2>Local Prediction Explanation</h2><p>Method: {explanation.method}</p><p>Prediction: {String(explanation.prediction)}</p>{explanation.prediction_probability !== null && <p>Prediction probability: {explanation.prediction_probability.toFixed(4)}</p>}{explanation.predicted_value !== null && <p>Predicted value: {String(explanation.predicted_value)}</p>}<Factors title="Factors increasing this output" factors={explanation.top_positive_factors} /><Factors title="Factors decreasing this output" factors={explanation.top_negative_factors} />{explanation.warnings.map((warning) => <p className="configuration-warning" key={warning}>{warning}</p>)}</section>;
}
