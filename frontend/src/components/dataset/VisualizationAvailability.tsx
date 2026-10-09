import type { DatasetProfile } from "../../types/profile";
import type { VisualInsights } from "../../services/profileService";

type Status = "ready" | "conditional" | "unavailable";
type Chart = { name: string; area: string; status: Status; message: string };

export default function VisualizationAvailability({ profile, insights }: { profile: DatasetProfile; insights: VisualInsights | null | undefined }) {
  const numeric = profile.summary.numerical_columns;
  const categorical = profile.summary.categorical_columns + profile.summary.boolean_columns;
  const dates = profile.summary.datetime_columns;
  const target = insights?.target;
  const charts: Chart[] = [
    { name: "Missingness chart", area: "Quality", status: profile.summary.missing_cells ? "ready" : "conditional", message: profile.summary.missing_cells ? "Columns with missing values are available." : "No missing values were detected." },
    { name: "Distribution histogram", area: "Numerical", status: numeric ? "ready" : "unavailable", message: numeric ? `${numeric} numerical feature(s) can be profiled.` : "Requires at least one numerical feature." },
    { name: "Boxplot / violin plot", area: "Numerical", status: numeric ? "ready" : "unavailable", message: numeric ? "Available for numerical spread and outlier review." : "Requires numerical values." },
    { name: "Correlation heatmap", area: "Relationships", status: numeric >= 2 ? "ready" : "unavailable", message: numeric >= 2 ? "At least two numerical features are available." : "Requires at least two numerical features." },
    { name: "Scatter plot", area: "Relationships", status: numeric >= 2 ? "ready" : "unavailable", message: numeric >= 2 ? "Feature-pair scatter plots can be generated." : "Requires at least two numerical features." },
    { name: "Categorical distribution", area: "Categorical", status: categorical ? "ready" : "unavailable", message: categorical ? `${categorical} categorical or boolean feature(s) are available.` : "Requires a categorical or boolean feature." },
    { name: "Categorical vs target", area: "Target analysis", status: target && categorical ? "ready" : "unavailable", message: target && categorical ? "Available for the configured target." : "Requires a configured target and categorical feature." },
    { name: "Class-balance chart", area: "Target analysis", status: insights?.problem_type === "classification" ? "ready" : "unavailable", message: insights?.problem_type === "classification" ? "Available for the configured classification target." : "Requires a configured classification target." },
    { name: "Feature–target ranking", area: "Target analysis", status: target && numeric ? "ready" : "unavailable", message: target && numeric ? "Numerical feature associations can be ranked." : "Requires a configured target and numerical feature." },
    { name: "Time trend", area: "Temporal", status: dates ? "ready" : "unavailable", message: dates ? `${dates} datetime feature(s) are available.` : "Requires a detected datetime column." },
    { name: "ROC / precision-recall", area: "Evaluation", status: insights?.problem_type === "classification" ? "conditional" : "unavailable", message: insights?.problem_type === "classification" ? "Available after a classifier has been trained." : "Requires a trained classification model." },
    { name: "Residual / actual vs predicted", area: "Evaluation", status: insights?.problem_type === "regression" ? "conditional" : "unavailable", message: insights?.problem_type === "regression" ? "Available after a regression model has been trained." : "Requires a trained regression model." },
    { name: "Cluster projection", area: "Evaluation", status: insights?.problem_type === "clustering" ? "conditional" : "unavailable", message: insights?.problem_type === "clustering" ? "Available after clustering has completed." : "Requires a clustering workflow." },
    { name: "Feature importance", area: "Explainability", status: target ? "conditional" : "unavailable", message: target ? "Available after a supervised model is trained." : "Requires a supervised target and trained model." },
  ];
  return <section className="visualization-availability intelligence-section"><div className="section-heading"><div><p className="eyebrow">VISUALIZATION CATALOGUE</p><h2>Graph availability</h2></div><p>Every chart is assessed against this dataset.</p></div><div className="visualization-grid">{charts.map((chart) => <article className={chart.status} key={chart.name}><div><span>{chart.area}</span><b>{chart.status === "ready" ? "Ready" : chart.status === "conditional" ? "After training" : "Not applicable"}</b></div><h3>{chart.name}</h3><p>{chart.message}</p></article>)}</div></section>;
}
