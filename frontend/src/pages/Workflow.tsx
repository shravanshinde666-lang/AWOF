import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import NodeDetails from "../components/workflow/NodeDetails";
import WorkflowGraph from "../components/workflow/WorkflowGraph";
import { getPrunedWorkflow, pruneWorkflow } from "../services/executionService";
import { generateWorkflow, getWorkflow } from "../services/workflowService";
import type { WorkflowNode, WorkflowResult } from "../types/workflow";

type PruningEvidence = {
  node_id: string;
  reason: string;
};

type PrunedWorkflow = {
  pruned_workflow_id: string;
  algorithm: string;
  algorithm_version: string;
  nodes: WorkflowNode[];
  edges: WorkflowResult["edges"];
  execution_order: string[];
  pruned_nodes: PruningEvidence[];
  summary: Record<string, number>;
  validation: WorkflowResult["validation"];
};

export default function Workflow() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState<WorkflowResult | null>(null);
  const [optimized, setOptimized] = useState<PrunedWorkflow | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  useEffect(() => {
    if (!datasetId) return;
    const id = datasetId;
    let active = true;

    async function load() {
      try {
        const current = await getWorkflow(id).catch(() => generateWorkflow(id));
        if (!active) return;
        setWorkflow(current);

        try {
          const previousOptimization = await getPrunedWorkflow(id);
          if (active) setOptimized(previousOptimization);
        } catch {
          // Optimization is optional until the user requests it.
        }
      } catch {
        if (active) setError("Workflow unavailable.");
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [datasetId]);

  async function optimize() {
    if (!datasetId) return;
    setIsOptimizing(true);
    setActionError(null);
    try {
      setOptimized(await pruneWorkflow(datasetId));
      setSelectedNode(null);
    } catch {
      setActionError("Unable to optimize the workflow. Please try again.");
    } finally {
      setIsOptimizing(false);
    }
  }

  if (error) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!workflow) return <main className="page">Generating adaptive workflow...</main>;

  const displayedWorkflow: WorkflowResult = optimized
    ? {
        ...workflow,
        workflow_id: optimized.pruned_workflow_id,
        algorithm: optimized.algorithm,
        algorithm_version: optimized.algorithm_version,
        nodes: optimized.nodes,
        edges: optimized.edges,
        execution_order: optimized.execution_order,
        summary: { ...workflow.summary, ...optimized.summary },
        validation: optimized.validation,
      }
    : workflow;

  return (
    <main className="page">
      <Link className="back-link" to={`/datasets/${datasetId}/capabilities`}>Back to capability scores</Link>
      <h1>{optimized ? "Optimized Adaptive Workflow" : "Adaptive Workflow Generated"}</h1>
      <p>
        Problem Type: {workflow.problem_type} · Total Nodes: {displayedWorkflow.summary.total_nodes} · Valid DAG: {displayedWorkflow.validation.is_dag ? "Yes" : "No"}
      </p>

      {!optimized && (
        <button type="button" onClick={optimize} disabled={isOptimizing}>
          {isOptimizing ? "Optimizing..." : "Optimize Workflow"}
        </button>
      )}
      {actionError && <p className="error-message">{actionError}</p>}

      {optimized && (
        <section aria-labelledby="optimization-result">
          <h2 id="optimization-result">Optimization result</h2>
          <p>{optimized.summary.pruned_nodes} node(s) pruned. The remaining workflow is ready to execute.</p>
          <button type="button" onClick={() => navigate(`/datasets/${datasetId}/execution`)}>
            Execute Workflow
          </button>
        </section>
      )}

      <WorkflowGraph workflow={displayedWorkflow} onSelect={setSelectedNode} />
      <NodeDetails node={selectedNode} />

      <h2>Execution Order</h2>
      <ol>
        {displayedWorkflow.execution_order.map((id) => <li key={id}>{displayedWorkflow.nodes.find((node) => node.id === id)?.label}</li>)}
      </ol>

      {optimized && (
        <details open>
          <summary>Pruned-node evidence ({optimized.pruned_nodes.length})</summary>
          {optimized.pruned_nodes.length === 0 ? (
            <p>No nodes were removed; every generated step remains relevant.</p>
          ) : (
            <ul>
              {optimized.pruned_nodes.map((node) => <li key={node.node_id}><strong>{node.node_id}</strong>: {node.reason}</li>)}
            </ul>
          )}
        </details>
      )}

      <details>
        <summary>Excluded by AWGA ({workflow.excluded_capabilities.length})</summary>
        {workflow.excluded_capabilities.map((capability) => <p key={capability.capability_id}>{capability.capability_id}: {capability.decision} — {capability.reason}</p>)}
      </details>
    </main>
  );
}
