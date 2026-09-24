import { Link, useLocation } from "react-router-dom";

const stages = [
  ["Intelligence", "intelligence"],
  ["Configure", "configure"],
  ["ACSA", "capabilities"],
  ["Workflow", "workflow"],
  ["Execute", "execution"],
  ["Models", "models"],
  ["Evaluate", "evaluation"],
  ["Explain", "explainability"],
  ["Priorities", "business"],
  ["Research", "research"],
] as const;

export default function Navbar() {
  const location = useLocation();
  const datasetId = location.pathname.match(/^\/datasets\/([^/]+)/)?.[1];
  const isActive = (segment: string) => location.pathname.endsWith(`/${segment}`);

  return (
    <header className="app-header">
      <div className="topbar">
        <Link className="brand" to="/" aria-label="AWOF home">
          <span className="brand-mark">A</span>
          <span><strong>AWOF</strong><small>Adaptive intelligence</small></span>
        </Link>
        <nav className="topbar-actions" aria-label="Primary navigation">
          <Link to="/">Overview</Link>
          <Link className="new-analysis" to="/upload">+ New analysis</Link>
        </nav>
      </div>
      {datasetId && (
        <nav className="stage-nav" aria-label="Analysis workflow">
          {stages.map(([label, segment], index) => (
            <Link key={segment} className={isActive(segment) ? "stage-link active" : "stage-link"} to={`/datasets/${datasetId}/${segment}`}>
              <span>{String(index + 1).padStart(2, "0")}</span>{label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
