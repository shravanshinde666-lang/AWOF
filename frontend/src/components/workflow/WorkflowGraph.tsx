import { Background, BackgroundVariant, Controls, MarkerType, MiniMap, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import WorkflowNode from "./WorkflowNode";
import type { WorkflowResult, WorkflowNode as AWGANode } from "../../types/workflow";
const nodeTypes = { workflow: WorkflowNode };
const NODE_WIDTH = 224;
const NODE_GAP_X = 92;
const NODE_GAP_Y = 46;

function layoutNodes(workflow: WorkflowResult): Node[] {
 const rank = new Map(workflow.nodes.map((node) => [node.id, 0]));
 for (let pass = 0; pass < workflow.nodes.length; pass += 1) {
  let changed = false;
  workflow.edges.forEach(({ source, target }) => {
   const next = (rank.get(source) ?? 0) + 1;
   if (next > (rank.get(target) ?? 0)) { rank.set(target, next); changed = true; }
  });
  if (!changed) break;
 }
 const layers = new Map<number, AWGANode[]>();
 workflow.nodes.forEach((node) => { const layer = rank.get(node.id) ?? 0; layers.set(layer, [...(layers.get(layer) ?? []), node]); });
 return Array.from(layers.entries()).flatMap(([layer, layerNodes]) => layerNodes.map((node, index) => ({
  id: node.id, type: "workflow", position: { x: layer * (NODE_WIDTH + NODE_GAP_X), y: index * (128 + NODE_GAP_Y) },
  data: { label: node.label, category: node.category, status: node.status, required: node.required },
 })));
}

export default function WorkflowGraph({workflow,onSelect}:{workflow:WorkflowResult;onSelect:(node:AWGANode)=>void}) {
 const nodes = layoutNodes(workflow);
 const edges:Edge[]=workflow.edges.map((edge)=>({id:`${edge.source}-${edge.target}`,source:edge.source,target:edge.target,type:"smoothstep",animated:true,markerEnd:{type:MarkerType.ArrowClosed,color:"#4de4c1",width:18,height:18},style:{stroke:"#4de4c1",strokeWidth:1.8}}));
 return <section className="workflow-canvas" aria-label="Adaptive workflow graph"><header className="workflow-canvas-header"><div><span>LIVE DAG</span><strong>Adaptive execution map</strong></div><p>{workflow.nodes.length} stages · {workflow.edges.length} dependencies</p></header><div className="workflow-graph"><ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{padding:0.22,maxZoom:1.1}} minZoom={0.35} maxZoom={1.5} defaultEdgeOptions={{type:"smoothstep"}} onNodeClick={(_,node)=>{const item=workflow.nodes.find(value=>value.id===node.id);if(item)onSelect(item);}}><Background variant={BackgroundVariant.Dots} gap={20} size={1}/><Controls showInteractive={false}/><MiniMap pannable zoomable nodeColor={(node)=>node.data.status==="optional"?"#e5a11d":"#b9ff2d"}/></ReactFlow></div></section>;
}
