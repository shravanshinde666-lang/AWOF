import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import CIPSCard from "../components/business/CIPSCard";
import CustomerPriorityTable from "../components/business/CustomerPriorityTable";
import { generateBusinessPriority, getBusinessPriority } from "../services/businessService";
import type { BusinessPriorityResult } from "../types/business";

export default function BusinessIntelligence() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [result, setResult] = useState<BusinessPriorityResult | null>(null);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (datasetId) void getBusinessPriority(datasetId).catch(() => generateBusinessPriority(datasetId)).then(setResult).catch(() => setError("Business priority analysis is unavailable.")); }, [datasetId]);
  const items = useMemo(() => result?.items.filter((item) => filter === "all" || item.priority_level === filter) ?? [], [filter, result]);
  if (error) return <main className="page"><p className="error-message">{error}</p><Link className="primary-link" to={`/datasets/${datasetId}/research`}>Run Research Comparison</Link></main>;
  if (!result) return <main className="page">Generating business priority analysis...</main>;
  if (result.applicability === "not_applicable") return <main className="page"><h1>Business Priority Analysis</h1><p>Business prioritization is not applicable to this workflow.</p><p>{result.warnings.join(" ")}</p><Link className="primary-link" to={`/datasets/${datasetId}/research`}>Run Research Comparison</Link></main>;
  return <main className="page"><h1>Business Priority Analysis</h1><p>Entities Scored: {result.summary.entities_scored} · Immediate: {result.summary.immediate_count} · High: {result.summary.high_count} · Medium: {result.summary.medium_count} · Monitor: {result.summary.monitor_count}</p><p>Applicability: {result.applicability}</p>{result.risk_direction_warning && <p className="configuration-warning">{result.risk_direction_warning}</p>}{result.items[0] && <CIPSCard item={result.items[0]} />}<label className="select-field">Priority filter<select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">All priorities</option><option value="immediate">Immediate</option><option value="high">High</option><option value="medium">Medium</option><option value="monitor">Monitor</option></select></label><CustomerPriorityTable items={items} /><Link className="primary-link" to={`/datasets/${datasetId}/research`}>Run Research Comparison</Link></main>;
}
