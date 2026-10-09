import { Link, useLocation } from "react-router-dom";

const links = [
  ["Overview", "⌂", "/"], ["Upload dataset", "⇧", "/upload"],
  ["Intelligence", "◉", "intelligence"], ["Configure", "⚙", "configure"],
  ["ACSA", "▦", "capabilities"], ["Workflow", "⌘", "workflow"],
  ["Execution", "✓", "execution"], ["Models", "◈", "models"],
  ["Evaluation", "▤", "evaluation"], ["Explainability", "◌", "explainability"],
  ["Priorities", "♧", "business"], ["Research", "⌁", "research"],
  ["Report", "R", "report"], ["History", "H", "history"],
] as const;

export default function Sidebar() {
  const location = useLocation();
  const datasetId = location.pathname.match(/^\/datasets\/([^/]+)/)?.[1];
  return <aside className="sidebar">
    <Link className="sidebar-brand" to="/"><span className="sidebar-mark">A</span><span><strong>AWOF</strong><small>Adaptive Workflow<br />Optimization Framework</small></span></Link>
    <nav className="sidebar-nav" aria-label="Application navigation">
      {links.map(([label, icon, destination]) => {
        const to = destination.startsWith("/") ? destination : datasetId ? `/datasets/${datasetId}/${destination}` : "/upload";
        const active = destination === "/" ? location.pathname === "/" : location.pathname.endsWith(`/${destination}`) || (destination === "/upload" && location.pathname === "/upload");
        return <Link className={active ? "sidebar-link active" : "sidebar-link"} to={to} key={label}><i>{icon}</i>{label}</Link>;
      })}
    </nav>
    <div className="sidebar-footer"><span className="status-chip success">● Ready</span><p>AWOF analytics workspace</p></div>
  </aside>;
}
