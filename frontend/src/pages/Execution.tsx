import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { executeWorkflow, getExecution } from "../services/executionService";
import { recommendModels } from "../services/modelService";

type Result = { summary: { initial_rows: number; final_rows: number; initial_columns: number; final_columns: number; executed_nodes: number; pruned_nodes: number; total_duration_ms: number }; node_results: Array<{ node_id: string; status: string; duration_ms: number }> };

export default function Execution() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<Result | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [recommending, setRecommending] = useState(false);

  useEffect(() => { if (datasetId) void getExecution(datasetId).catch(() => executeWorkflow(datasetId)).then(setResult); }, [datasetId]);
  async function recommend() {
    if (!datasetId) return;
    setRecommending(true); setRecommendationError(null);
    try { await recommendModels(datasetId); navigate(`/datasets/${datasetId}/models`); }
    catch { setRecommendationError("Model recommendations could not be generated."); }
    finally { setRecommending(false); }
  }
  return <main className="page"><h1>Workflow Execution</h1>{result && <><p>Rows: {result.summary.initial_rows} → {result.summary.final_rows}; Features: {result.summary.initial_columns} → {result.summary.final_columns}</p><p>Executed: {result.summary.executed_nodes}; Pruned: {result.summary.pruned_nodes}; Duration: {result.summary.total_duration_ms} ms</p><ol>{result.node_results.map((node) => <li key={node.node_id}>{node.node_id}: {node.status} ({node.duration_ms} ms)</li>)}</ol><button type="button" onClick={recommend} disabled={recommending}>{recommending ? "Running AMRA..." : "Recommend Models"}</button>{recommendationError && <p className="error-message">{recommendationError}</p>}</>}</main>;
}
