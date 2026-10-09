import type { FeatureImportanceItem } from "../../types/explainability";

export default function FeatureImportance({ items }: { items: FeatureImportanceItem[] }) {
  const maximum = Math.max(...items.map((item) => item.importance), 1);
  return <section className="card importance-panel"><div className="section-heading"><div><p className="eyebrow">GLOBAL VIEW</p><h2>Feature importance</h2></div><p>{items.length} ranked model inputs</p></div><p className="importance-intro">Longer bars indicate a stronger influence on the model. Direction is shown only when the explanation method can support it.</p><div className="importance-list">{items.map((item) => <div className="importance-row" key={item.feature}><span><b>{item.rank}</b>{item.feature}</span><div className="importance-track"><span style={{ width: `${item.importance / maximum * 100}%` }} /></div><small>{item.importance.toFixed(4)}{item.direction ? <em className={item.direction === "positive" ? "positive" : "negative"}>{item.direction}</em> : null}</small></div>)}</div></section>;
}
