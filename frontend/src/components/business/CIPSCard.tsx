import type { CIPSResultItem } from "../../types/business";

export default function CIPSCard({ item }: { item: CIPSResultItem }) {
  return <article className="card"><h2>Highest Priority Entity</h2><p>CIPS Score: {item.cips_score.toFixed(2)}</p><p>Priority: {item.priority_level}</p>{item.risk_probability !== null && <p>Risk: {item.risk_probability.toFixed(4)}</p>}<p>{item.top_reasons.join(" · ")}</p><p>{item.recommended_action}</p></article>;
}
