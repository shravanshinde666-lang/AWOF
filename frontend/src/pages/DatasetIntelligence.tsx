import { AxiosError } from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Loading from "../components/common/Loading";
import VisualDashboard from "../components/dataset/VisualDashboard";
import VisualizationAvailability from "../components/dataset/VisualizationAvailability";
import { getDataset, type DatasetMetadata } from "../services/datasetService";
import { getProfile, getVisualInsights, type VisualInsights } from "../services/profileService";
import type {
  ColumnProfile,
  ColumnTypeInfo,
  DatasetProfile,
  DistributionInfo,
  NumericStatistics,
  ProfileValue,
} from "../types/profile";

type IntelligenceTab =
  | "overview"
  | "columns"
  | "statistics"
  | "missing"
  | "outliers"
  | "correlations"
  | "distributions"
  | "advanced";

interface ProfileColumnEntry {
  typeInfo: ColumnTypeInfo;
  profile: ColumnProfile;
}

const tabs: Array<{ id: IntelligenceTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "columns", label: "Columns" },
  { id: "statistics", label: "Statistics" },
  { id: "missing", label: "Missing Values" },
  { id: "outliers", label: "Outliers" },
  { id: "correlations", label: "Correlations" },
  { id: "distributions", label: "Distributions" },
  { id: "advanced", label: "Advanced EDA" },
];

function formatNumber(value: number | null | undefined, maximumFractionDigits = 2): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(value);
}

function formatPercent(value: number | null | undefined): string {
  return value == null || !Number.isFinite(value) ? "—" : `${formatNumber(value, 2)}%`;
}

function formatValue(value: ProfileValue | undefined): string {
  if (value == null) return "—";
  return typeof value === "number" ? formatNumber(value, 4) : String(value);
}

function formatMemory(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${formatNumber(value, 2)} ${units[unitIndex]}`;
}

function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function clampPercentage(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function getErrorMessage(cause: unknown, fallback: string): string {
  if (cause instanceof AxiosError) {
    const data = cause.response?.data;
    if (data && typeof data === "object") {
      const message = (data as { error?: unknown; detail?: unknown }).error
        ?? (data as { detail?: unknown }).detail;
      if (typeof message === "string") return message;
    }
  }
  return fallback;
}

function getProfileColumns(profile: DatasetProfile): ProfileColumnEntry[] {
  return profile.column_types.flatMap((typeInfo) => {
    const columnProfile = profile.columns[typeInfo.column];
    return columnProfile ? [{ typeInfo, profile: columnProfile }] : [];
  });
}

function OverviewSection({ profile }: { profile: DatasetProfile }) {
  const { summary, quality } = profile;
  const cards = [
    ["Rows", formatNumber(summary.rows, 0)],
    ["Columns", formatNumber(summary.columns, 0)],
    ["Numerical", formatNumber(summary.numerical_columns, 0)],
    ["Categorical", formatNumber(summary.categorical_columns, 0)],
    ["Boolean", formatNumber(summary.boolean_columns, 0)],
    ["Datetime", formatNumber(summary.datetime_columns, 0)],
    ["Text", formatNumber(summary.text_columns, 0)],
    ["Missing", formatPercent(summary.missing_percentage)],
    ["Duplicates", formatNumber(summary.duplicate_rows, 0)],
    ["Memory Usage", formatMemory(summary.memory_usage_bytes)],
  ];
  const qualitySignals = [
    ["Columns with missing values", quality.summary.columns_with_missing_values],
    ["Constant columns", quality.summary.constant_columns],
    ["High-cardinality columns", quality.summary.high_cardinality_columns],
    ["Columns with outliers", quality.summary.columns_with_outliers],
  ] as const;

  return (
    <section className="intelligence-section" aria-labelledby="overview-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Dataset summary</p>
          <h2 id="overview-heading">Overview</h2>
        </div>
        <p>{formatNumber(summary.total_cells, 0)} total cells</p>
      </div>
      <div className="summary-grid intelligence-summary-grid">
        {cards.map(([label, value]) => (
          <article className="summary-card" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
      <div className="quality-signals" aria-label="Data quality signals">
        {qualitySignals.map(([label, value]) => (
          <p key={label}><span>{label}</span><strong>{formatNumber(value, 0)}</strong></p>
        ))}
      </div>
    </section>
  );
}

function ColumnTypesSection({ entries }: { entries: ProfileColumnEntry[] }) {
  return (
    <section className="intelligence-section" aria-labelledby="columns-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Automatic detection</p>
          <h2 id="columns-heading">Column types and cardinality</h2>
        </div>
        <p>Type detection is heuristic and should be reviewed in context.</p>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Column</th>
              <th>Pandas Type</th>
              <th>Detected Type</th>
              <th>Unique Values</th>
              <th>Unique %</th>
              <th>Missing %</th>
              <th>Cardinality</th>
              <th>Signals</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(({ typeInfo, profile }) => (
              <tr key={typeInfo.column}>
                <td><code>{typeInfo.column}</code></td>
                <td>{typeInfo.pandas_dtype}</td>
                <td><span className="type-badge">{humanize(typeInfo.detected_type)}</span></td>
                <td>{formatNumber(typeInfo.unique_count, 0)}</td>
                <td>{formatPercent(typeInfo.unique_percentage)}</td>
                <td>{formatPercent(profile.missing.missing_percentage)}</td>
                <td>{humanize(typeInfo.cardinality)}</td>
                <td>
                  {typeInfo.is_constant && <span className="signal-badge">Constant</span>}
                  {typeInfo.is_identifier_candidate && <span className="signal-badge">ID candidate</span>}
                  {!typeInfo.is_constant && !typeInfo.is_identifier_candidate && "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StatisticsSection({ entries }: { entries: ProfileColumnEntry[] }) {
  const numericEntries = entries.filter(({ profile }) => profile.numeric_statistics !== null);

  if (numericEntries.length === 0) {
    return <EmptySection title="Statistical summary" message="No numerical columns were detected for statistical profiling." />;
  }

  const statisticValue = (statistics: NumericStatistics, key: keyof NumericStatistics) => {
    const value = statistics[key];
    return typeof value === "number" ? formatNumber(value, 4) : formatValue(value as ProfileValue);
  };

  const columns: Array<[string, keyof NumericStatistics]> = [
    ["Mean", "mean"], ["Median", "median"], ["Mode", "mode"], ["Min", "minimum"],
    ["Max", "maximum"], ["Range", "range"], ["Variance", "variance"],
    ["Std Dev", "standard_deviation"], ["Q1", "q1"], ["Q3", "q3"],
    ["IQR", "iqr"], ["Skewness", "skewness"],
  ];

  return (
    <section className="intelligence-section" aria-labelledby="statistics-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Measures of center and spread</p>
          <h2 id="statistics-heading">Statistical summary</h2>
        </div>
        <p>Values are rounded for display only.</p>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Column</th>
              {columns.map(([label]) => <th key={label}>{label}</th>)}
            </tr>
          </thead>
          <tbody>
            {numericEntries.map(({ typeInfo, profile }) => {
              const statistics = profile.numeric_statistics;
              if (!statistics) return null;
              return (
                <tr key={typeInfo.column}>
                  <td><code>{typeInfo.column}</code></td>
                  {columns.map(([label, key]) => <td key={label}>{statisticValue(statistics, key)}</td>)}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function MissingValuesSection({ entries }: { entries: ProfileColumnEntry[] }) {
  return (
    <section className="intelligence-section" aria-labelledby="missing-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Detection only</p>
          <h2 id="missing-heading">Missing values</h2>
        </div>
        <p>No imputation or cleaning has been applied.</p>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Column</th><th>Missing Count</th><th>Missing %</th><th>Severity</th><th>Distribution</th></tr></thead>
          <tbody>
            {entries.map(({ typeInfo, profile }) => {
              const missing = profile.missing;
              const percentage = clampPercentage(missing.missing_percentage);
              return (
                <tr key={typeInfo.column}>
                  <td><code>{typeInfo.column}</code></td>
                  <td>{formatNumber(missing.missing_count, 0)}</td>
                  <td>{formatPercent(missing.missing_percentage)}</td>
                  <td><span className="type-badge">{humanize(missing.severity)}</span></td>
                  <td>
                    <div className="percentage-bar" aria-label={`${formatPercent(missing.missing_percentage)} missing`}>
                      <span style={{ width: `${percentage}%` }} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function OutliersSection({ entries }: { entries: ProfileColumnEntry[] }) {
  const outlierEntries = entries.filter(({ profile }) => profile.outliers !== null);
  if (outlierEntries.length === 0) {
    return <EmptySection title="Outlier detection" message="No numerical columns were suitable for IQR outlier analysis." />;
  }

  return (
    <section className="intelligence-section" aria-labelledby="outliers-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Detection only</p>
          <h2 id="outliers-heading">Outlier detection</h2>
        </div>
        <p>Outliers are detected using the IQR method; no values were removed.</p>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Column</th><th>Outlier Count</th><th>Outlier %</th><th>Lower Bound</th><th>Upper Bound</th></tr></thead>
          <tbody>
            {outlierEntries.map(({ typeInfo, profile }) => {
              const outliers = profile.outliers;
              if (!outliers) return null;
              return (
                <tr key={typeInfo.column}>
                  <td><code>{typeInfo.column}</code></td>
                  <td>{formatNumber(outliers.outlier_count, 0)}</td>
                  <td>{formatPercent(outliers.outlier_percentage)}</td>
                  <td>{formatNumber(outliers.lower_bound, 4)}</td>
                  <td>{formatNumber(outliers.upper_bound, 4)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CorrelationsSection({ profile }: { profile: DatasetProfile }) {
  const pairs = [...profile.correlations.pairs]
    .filter((pair) => pair.correlation !== null)
    .sort((left, right) => Math.abs(right.correlation ?? 0) - Math.abs(left.correlation ?? 0));

  if (pairs.length === 0) {
    return <EmptySection title="Correlation analysis" message="No valid numerical correlation pairs were available for this dataset." />;
  }

  return (
    <section className="intelligence-section" aria-labelledby="correlations-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{humanize(profile.correlations.method)} correlation</p>
          <h2 id="correlations-heading">Numerical correlations</h2>
        </div>
        <p>Correlation describes association, not causation.</p>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Feature A</th><th>Feature B</th><th>Correlation</th><th>Strength</th></tr></thead>
          <tbody>
            {pairs.map((pair) => (
              <tr key={`${pair.feature_1}-${pair.feature_2}`}>
                <td><code>{pair.feature_1}</code></td>
                <td><code>{pair.feature_2}</code></td>
                <td>{formatNumber(pair.correlation, 4)}</td>
                <td>{humanize(pair.strength ?? undefined)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Histogram({ distribution }: { distribution: DistributionInfo }) {
  const histogram = distribution.histogram;
  if (!histogram || histogram.counts.length === 0) {
    return <p className="empty-state">Histogram data is not available for this column.</p>;
  }
  const maxCount = Math.max(...histogram.counts, 1);

  return (
    <div className="histogram" role="img" aria-label="Histogram generated from the selected column">
      <div className="histogram-bars">
        {histogram.counts.map((count, index) => {
          const start = histogram.bin_edges[index];
          const end = histogram.bin_edges[index + 1];
          const height = Math.max(3, (count / maxCount) * 100);
          const label = `${formatNumber(start, 2)} – ${formatNumber(end, 2)}`;
          return (
            <div className="histogram-bin" key={`${label}-${index}`} title={`${label}: ${formatNumber(count, 0)} values`}>
              <span className="histogram-count">{formatNumber(count, 0)}</span>
              <div className="histogram-bar" style={{ height: `${height}%` }} />
              <span className="histogram-label">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DistributionsSection({ entries }: { entries: ProfileColumnEntry[] }) {
  const distributionEntries = entries.filter(({ profile }) => profile.distribution?.histogram !== null && profile.distribution?.histogram !== undefined);
  const [selectedColumn, setSelectedColumn] = useState("");

  useEffect(() => {
    if (!distributionEntries.some(({ typeInfo }) => typeInfo.column === selectedColumn)) {
      setSelectedColumn(distributionEntries[0]?.typeInfo.column ?? "");
    }
  }, [distributionEntries, selectedColumn]);

  if (distributionEntries.length === 0) {
    return <EmptySection title="Distribution analysis" message="No numerical columns with histogram data were available." />;
  }

  const selected = distributionEntries.find(({ typeInfo }) => typeInfo.column === selectedColumn) ?? distributionEntries[0];
  const distribution = selected.profile.distribution;
  if (!distribution) return null;

  return (
    <section className="intelligence-section" aria-labelledby="distributions-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Aggregated histogram</p>
          <h2 id="distributions-heading">Distribution analysis</h2>
        </div>
        <p>Histogram bins are calculated from the uploaded dataset.</p>
      </div>
      <label className="select-field" htmlFor="distribution-column">
        <span>Select numerical column</span>
        <select id="distribution-column" value={selected.typeInfo.column} onChange={(event) => setSelectedColumn(event.target.value)}>
          {distributionEntries.map(({ typeInfo }) => <option key={typeInfo.column} value={typeInfo.column}>{typeInfo.column}</option>)}
        </select>
      </label>
      <p className="distribution-shape">Observed shape: <strong>{humanize(distribution.distribution_shape)}</strong></p>
      <Histogram distribution={distribution} />
    </section>
  );
}

function AdvancedEdaSection({ entries, insights, profile }: { entries: ProfileColumnEntry[]; insights: VisualInsights | null; profile: DatasetProfile }) {
  const numeric = entries
    .filter(({ profile }) => profile.numeric_statistics !== null)
    .map(({ typeInfo, profile }) => ({ column: typeInfo.column, statistics: profile.numeric_statistics!, outliers: profile.outliers }));
  const categorical = entries.filter(({ profile }) => (profile.categorical_statistics?.top_values.length ?? 0) > 0);
  const missingPatterns = profile.quality.missing_values.patterns;

  const normality = (statistics: NumericStatistics) => {
    const skewness = statistics.skewness;
    const kurtosis = statistics.kurtosis;
    if (skewness == null || kurtosis == null) return "Insufficient data";
    return Math.abs(skewness) <= 0.5 && Math.abs(kurtosis) <= 1 ? "Approximately symmetric" : "Non-normal / skewed";
  };

  return (
    <section className="intelligence-section" aria-labelledby="advanced-eda-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">DATA-AWARE DIAGNOSTICS</p>
          <h2 id="advanced-eda-heading">Advanced exploratory analysis</h2>
        </div>
        <p>Only diagnostics supported by the uploaded dataset are shown.</p>
      </div>

      {numeric.length > 0 ? <div className="table-scroll"><table>
        <thead><tr><th>Feature</th><th>Skewness</th><th>Kurtosis</th><th>Shape</th><th>Normality signal</th><th>IQR outliers</th></tr></thead>
        <tbody>{numeric.map(({ column, statistics, outliers }) => <tr key={column}>
          <td><code>{column}</code></td><td>{formatNumber(statistics.skewness, 3)}</td><td>{formatNumber(statistics.kurtosis, 3)}</td>
          <td>{humanize(entries.find((entry) => entry.typeInfo.column === column)?.profile.distribution?.distribution_shape)}</td>
          <td><span className="type-badge">{normality(statistics)}</span></td><td>{outliers ? `${formatNumber(outliers.outlier_count, 0)} (${formatPercent(outliers.outlier_percentage)})` : "â€”"}</td>
        </tr>)}</tbody>
      </table></div> : <p className="empty-state">Not applicable: numerical diagnostics require at least one numerical feature.</p>}

      <div className="advanced-eda-grid">
        <article><h3>Categorical concentration</h3>{categorical.length ? <ul>{categorical.slice(0, 6).map(({ typeInfo, profile }) => {
          const top = profile.categorical_statistics?.top_values[0];
          return <li key={typeInfo.column}><code>{typeInfo.column}</code><span>{top ? `${formatValue(top.value)} (${formatPercent(top.percentage)})` : "No values"}</span></li>;
        })}</ul> : <p className="empty-state">Not applicable: no categorical features were detected.</p>}</article>
        <article><h3>Target diagnostics</h3>{insights?.target ? <ul>
          <li><span>Configured target</span><strong>{insights.target}</strong></li>
          <li><span>Problem type</span><strong>{insights.problem_type ? humanize(insights.problem_type) : "Pending"}</strong></li>
          <li><span>Target distribution</span><strong>{insights.target_distribution.length ? `${insights.target_distribution.length} group(s)` : "Not available"}</strong></li>
          <li><span>Categorical vs target</span><strong>{insights.category_target_rates.length ? "Available" : "Not applicable"}</strong></li>
        </ul> : <p className="empty-state">Not applicable: configure a target to unlock target-aware EDA.</p>}</article>
        <article><h3>Missingness patterns</h3>{missingPatterns?.patterns.length ? <ul>{missingPatterns.patterns.slice(0, 5).map((pattern) => <li key={pattern.columns.join("|")}><span title={pattern.columns.join(", ")}>{pattern.columns.join(", ")}</span><strong>{formatNumber(pattern.row_count, 0)} rows ({formatPercent(pattern.percentage)})</strong></li>)}</ul> : <p className="empty-state">No co-occurring missing-value patterns were detected.</p>}</article>
        <article><h3>Featureâ€“target relevance</h3>{insights?.feature_target_ranking.items.length ? <ul>{insights.feature_target_ranking.items.slice(0, 8).map((item) => <li key={item.feature}><code>{item.feature}</code><strong>{formatNumber(item.score, 4)}</strong></li>)}</ul> : <p className="empty-state">{insights?.feature_target_ranking.message ?? "Not applicable: configure a supervised target first."}</p>}<small>Mutual-information scores rank association strength; they do not imply causation.</small></article>
      </div>
    </section>
  );
}

function EmptySection({ title, message }: { title: string; message: string }) {
  return (
    <section className="intelligence-section empty-intelligence-section">
      <h2>{title}</h2>
      <p className="empty-state">{message}</p>
    </section>
  );
}

export default function DatasetIntelligence() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [dataset, setDataset] = useState<DatasetMetadata | null>(null);
  const [insights, setInsights] = useState<VisualInsights | null>(null);
  const [activeTab, setActiveTab] = useState<IntelligenceTab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    if (!datasetId) {
      setError("A dataset identifier is required to view intelligence results.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [loadedProfile, loadedDataset, loadedInsights] = await Promise.all([
        getProfile(datasetId),
        getDataset(datasetId).catch(() => null),
        getVisualInsights(datasetId).catch(() => null),
      ]);
      setProfile(loadedProfile);
      setDataset(loadedDataset);
      setInsights(loadedInsights);
    } catch (cause) {
      setProfile(null);
      setError(getErrorMessage(cause, "Unable to load this dataset profile."));
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const entries = useMemo(() => profile ? getProfileColumns(profile) : [], [profile]);

  const content = (() => {
    if (!profile) return null;
    switch (activeTab) {
      case "columns": return <ColumnTypesSection entries={entries} />;
      case "statistics": return <StatisticsSection entries={entries} />;
      case "missing": return <MissingValuesSection entries={entries} />;
      case "outliers": return <OutliersSection entries={entries} />;
      case "correlations": return <CorrelationsSection profile={profile} />;
      case "distributions": return <DistributionsSection entries={entries} />;
      case "advanced": return <AdvancedEdaSection entries={entries} insights={insights} profile={profile} />;
      default: return <><VisualDashboard profile={profile} dataset={dataset} insights={insights} /><VisualizationAvailability profile={profile} insights={insights} /><OverviewSection profile={profile} /></>;
    }
  })();

  return (
    <main className="page intelligence-page">
      <Link className="back-link" to="/upload">← Upload another dataset</Link>
      <header className="intelligence-header">
        <div>
          <p className="eyebrow">AWOF</p>
          <h1>Dataset Intelligence</h1>
          <p>{dataset?.original_filename ?? "Uploaded dataset"}</p>
        </div>
        <div>
          {profile && <p className="generated-at">Profile generated {formatGeneratedAt(profile.generated_at)}</p>}
          {profile && datasetId && <Link className="primary-link configure-link" to={`/datasets/${encodeURIComponent(datasetId)}/configure`}>Configure Analysis</Link>}
        </div>
      </header>

      {loading && <Loading message="Loading dataset intelligence..." />}

      {error && (
        <section className="intelligence-alert" role="alert">
          <h2>Profile unavailable</h2>
          <p>{error}</p>
          <p>Generate a profile from the Upload Dataset page, then return here.</p>
          <button type="button" onClick={() => void loadProfile()}>Retry</button>
        </section>
      )}

      {profile && !loading && (
        <>
          <nav className="intelligence-tabs" aria-label="Dataset intelligence sections" role="tablist">
            {tabs.map((tab) => (
              <button
                className={activeTab === tab.id ? "tab-button active" : "tab-button"}
                id={`tab-${tab.id}`}
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
          <div id={`panel-${activeTab}`} role="tabpanel" aria-labelledby={`tab-${activeTab}`}>
            {content}
          </div>
        </>
      )}
    </main>
  );
}
