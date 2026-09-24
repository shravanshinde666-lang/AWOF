import type { FeatureImportanceItem } from "../../types/explainability";

export default function FeatureImportance({ items }: { items: FeatureImportanceItem[] }) {
  const maximum = Math.max(...items.map((item) => item.importance), 1);
  return <section><h2>Global Feature Importance</h2>{items.map((item) => <div className="importance-row" key={item.feature}><span>{item.rank}. {item.feature}</span><div className="importance-track"><span style={{ width: `${item.importance / maximum * 100}%` }} /></div><small>{item.importance.toFixed(4)}{item.direction ? ` (${item.direction})` : ""}</small></div>)}</section>;
}
