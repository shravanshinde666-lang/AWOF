import type { CIPSResultItem } from "../../types/business";

export default function CustomerPriorityTable({ items }: { items: CIPSResultItem[] }) {
  return <div className="table-scroll"><table><thead><tr><th>Entity</th><th>Prediction</th><th>Risk</th><th>Business Value</th><th>CIPS</th><th>Priority</th><th>Main Reason</th><th>Recommended Action</th></tr></thead><tbody>{items.map((item) => <tr key={item.row_index}><td>{item.entity_id ?? `Row ${item.row_index}`}</td><td>{String(item.prediction)}</td><td>{item.risk_probability === null ? "Not available" : item.risk_probability.toFixed(4)}</td><td>{item.signals.business_value === undefined ? "Not available" : item.signals.business_value.toFixed(4)}</td><td>{item.cips_score.toFixed(2)}</td><td>{item.priority_level}</td><td>{item.top_reasons[0]}</td><td>{item.recommended_action}</td></tr>)}</tbody></table></div>;
}
