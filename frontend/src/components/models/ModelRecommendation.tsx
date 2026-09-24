import type { ModelRecommendation as Recommendation } from "../../types/model";

export default function ModelRecommendation({ model }: { model: Recommendation }) {
  return (
    <article className="card">
      <h3>{model.label}</h3>
      <p>AMRA suitability: {(model.score * 100).toFixed(0)}%</p>
      <p>Rank: {model.rank ? `#${model.rank}` : "Unavailable"}</p>
      <p>Decision: {model.decision.replace("_", " ")}</p>
      <p>Estimated complexity: {model.estimated_complexity}</p>
      <ul>{model.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
    </article>
  );
}
