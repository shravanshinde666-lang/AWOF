import { Background, Controls, MarkerType, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import WorkflowNode from "./WorkflowNode";
import type { WorkflowResult, WorkflowNode as AWGANode } from "../../types/workflow";
const types={workflow:WorkflowNode};
export default function WorkflowGraph({workflow,onSelect}:{workflow:WorkflowResult;onSelect:(node:AWGANode)=>void}) {
 const nodes:Node[]=workflow.nodes.map((node,index)=>({id:node.id,type:"workflow",position:{x:(index%4)*240,y:Math.floor(index/4)*145},data:{label:node.label,category:node.category,status:node.status}}));
 const edges:Edge[]=workflow.edges.map((edge)=>({id:`${edge.source}-${edge.target}`,source:edge.source,target:edge.target,markerEnd:{type:MarkerType.ArrowClosed,color:"#3b82f6"},style:{stroke:"#7aa7eb",strokeWidth:2}}));
 return <div className="workflow-graph"><ReactFlow nodes={nodes} edges={edges} nodeTypes={types} fitView onNodeClick={(_,node)=>{const item=workflow.nodes.find(value=>value.id===node.id);if(item)onSelect(item);}}><Background/><Controls/></ReactFlow></div>;
}
