import type { DatasetMetadata } from "../../services/datasetService";
import type { ColumnProfile, DatasetProfile, ProfileValue } from "../../types/profile";

function num(value: number | null | undefined, digits = 0): string {
  return value == null || !Number.isFinite(value) ? "—" : new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(value);
}

function text(value: ProfileValue | undefined): string { return value == null ? "—" : String(value); }

export default function VisualDashboard({ profile, dataset }: { profile: DatasetProfile; dataset: DatasetMetadata | null }) {
  const { summary, quality } = profile;
  const total = Math.max(summary.columns, 1);
  const numericPct = summary.numerical_columns / total * 100;
  const categoryPct = summary.categorical_columns / total * 100;
  const donut = `conic-gradient(#3478f6 0 ${numericPct}%, #35b878 ${numericPct}% ${numericPct + categoryPct}%, #f1ae3c ${numericPct + categoryPct}% 100%)`;
  const getColumn = (column: string): ColumnProfile | undefined => profile.columns[column];
  const identifier = profile.column_types.find((item) => item.is_identifier_candidate)?.column;
  const numeric = profile.column_types.map((item) => [item.column, getColumn(item.column)] as const).filter((entry): entry is readonly [string, ColumnProfile] => Boolean(entry[1]?.numeric_statistics)).slice(0, 4);
  const category = profile.column_types.map((item) => [item.column, getColumn(item.column)] as const).find((entry): entry is readonly [string, ColumnProfile] => Boolean(entry[1]?.categorical_statistics?.top_values.length));
  const topValues = category?.[1].categorical_statistics?.top_values.slice(0, 5) ?? [];
  const correlations = [...profile.correlations.pairs].filter((pair) => pair.correlation !== null).sort((a, b) => Math.abs(b.correlation ?? 0) - Math.abs(a.correlation ?? 0)).slice(0, 5);
  const metrics = [["Rows", num(summary.rows), "Records", "blue"], ["Columns", num(summary.columns), "Attributes", "green"], ["Missing", `${summary.missing_percentage.toFixed(1)}%`, "Completeness", "red"], ["Duplicates", num(summary.duplicate_rows), "Repeated rows", "amber"]];

  return <section className="visual-dashboard" aria-label="Dataset visual dashboard">
    <div className="dashboard-title-row"><div><p className="eyebrow">VISUAL DATA BRIEF</p><h2>Dataset at a glance</h2><p>{dataset?.original_filename ?? "Uploaded dataset"} · Real profile insights</p></div><span className="dashboard-status">● Profile complete</span></div>
    <div className="metric-grid">{metrics.map(([label, metric, hint, tone]) => <article className={`metric-card ${tone}`} key={label}><span>{label}</span><strong>{metric}</strong><small>{hint}</small></article>)}</div>
    <div className="dashboard-grid dashboard-grid-primary">
      <article className="dashboard-card"><div className="card-title"><div><span className="card-kicker">DATASET OVERVIEW</span><h3>Profile summary</h3></div></div><dl className="overview-list"><div><dt>Total cells</dt><dd>{num(summary.total_cells)}</dd></div><div><dt>Identifier</dt><dd>{identifier ?? "Not detected"}</dd></div><div><dt>Memory usage</dt><dd>{num(summary.memory_usage_bytes / 1024 / 1024, 2)} MB</dd></div><div><dt>Outlier columns</dt><dd>{num(quality.summary.columns_with_outliers)}</dd></div></dl></article>
      <article className="dashboard-card"><div className="card-title"><div><span className="card-kicker">ATTRIBUTE MIX</span><h3>Detected data types</h3></div></div><div className="donut-layout"><div className="type-donut" style={{ background: donut }}><span><strong>{num(summary.columns)}</strong>columns</span></div><ul className="chart-legend"><li><i className="legend-blue" />Numerical <b>{num(summary.numerical_columns)}</b></li><li><i className="legend-green" />Categorical <b>{num(summary.categorical_columns)}</b></li><li><i className="legend-amber" />Other <b>{num(summary.boolean_columns + summary.datetime_columns + summary.text_columns)}</b></li></ul></div></article>
      <article className="dashboard-card"><div className="card-title"><div><span className="card-kicker">QUALITY SIGNALS</span><h3>Readiness checks</h3></div></div><div className="quality-score"><span>{Math.max(0, 100 - summary.missing_percentage - summary.duplicate_percentage).toFixed(0)}</span><small>data quality score</small></div><ul className="quality-list"><li><span>Missing-value columns</span><b>{num(quality.summary.columns_with_missing_values)}</b></li><li><span>High-cardinality columns</span><b>{num(quality.summary.high_cardinality_columns)}</b></li><li><span>Constant columns</span><b>{num(quality.summary.constant_columns)}</b></li></ul></article>
    </div>
    <div className="dashboard-grid dashboard-grid-secondary">
      <article className="dashboard-card"><div className="card-title"><div><span className="card-kicker">RELATIONSHIPS</span><h3>Important correlations</h3></div><small>{profile.correlations.method}</small></div>{correlations.length ? <div className="correlation-bars">{correlations.map((pair) => <div className="correlation-row" key={`${pair.feature_1}-${pair.feature_2}`}><span>{pair.feature_1} ↔ {pair.feature_2}</span><div><i className={pair.correlation && pair.correlation < 0 ? "negative" : ""} style={{ width: `${Math.abs(pair.correlation ?? 0) * 100}%` }} /></div><b>{(pair.correlation ?? 0).toFixed(3)}</b></div>)}</div> : <p className="chart-empty">No numerical correlation pairs are available.</p>}</article>
      <article className="dashboard-card"><div className="card-title"><div><span className="card-kicker">CATEGORICAL DISTRIBUTION</span><h3>{category?.[0] ?? "No categorical column"}</h3></div><small>Top values</small></div>{topValues.length ? <div className="vertical-bars">{topValues.map((item, index) => <div className="vertical-bar" key={`${text(item.value)}-${index}`}><span>{num(item.count)}</span><i style={{ height: `${Math.max(5, item.percentage)}%` }} /><small title={text(item.value)}>{text(item.value)}</small></div>)}</div> : <p className="chart-empty">No categorical distribution is available.</p>}</article>
    </div>
    <article className="dashboard-card statistics-card"><div className="card-title"><div><span className="card-kicker">NUMERICAL PROFILE</span><h3>Key numerical statistics</h3></div><small>Real profile values</small></div>{numeric.length ? <div className="table-scroll"><table><thead><tr><th>Feature</th><th>Mean</th><th>Median</th><th>Min</th><th>Max</th><th>Std. deviation</th></tr></thead><tbody>{numeric.map(([column, item]) => { const stats = item.numeric_statistics; return stats && <tr key={column}><td><code>{column}</code></td><td>{num(stats.mean, 3)}</td><td>{num(stats.median, 3)}</td><td>{num(stats.minimum, 3)}</td><td>{num(stats.maximum, 3)}</td><td>{num(stats.standard_deviation, 3)}</td></tr>; })}</tbody></table></div> : <p className="chart-empty">No numerical statistics are available.</p>}</article>
  </section>;
}
