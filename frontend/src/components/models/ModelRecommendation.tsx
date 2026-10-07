import type { ModelRecommendation as Recommendation } from "../../types/model";

export default function ModelRecommendation({ model }: { model: Recommendation }) {
  return <article className={`card model-card ${model.decision}`}>
    <div className="model-card-head"><div><span className="card-kicker">{model.rank ? `RANK #${model.rank}` : "UNAVAILABLE"}</span><h3>{model.label}</h3></div><span className={`decision ${model.decision}`}>{model.decision.replace("_", " ")}</span></div>
    <div className="model-score"><strong>{(model.score * 100).toFixed(0)}%</strong><span>AMRA suitability</span></div><div className="capability-bar"><span style={{ width: `${model.score * 100}%` }} /></div>
    <p className="model-complexity">Estimated complexity: <strong>{model.estimated_complexity}</strong></p><ul>{model.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
  </article>;
}
