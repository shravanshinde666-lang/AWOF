import { type NodeProps } from "@xyflow/react";
export default function WorkflowNode({ data }: NodeProps) { const d=data as {label:string;category:string;status:string}; return <div className="workflow-node"><strong>{d.label}</strong><small>{d.category}</small><small>ACSA: {d.status.toUpperCase()}</small></div>; }
