from .node import WorkflowNode
class WorkflowGraph:
 def __init__(self): self.nodes={}; self.edges=[]
 def add_node(self,n:WorkflowNode):
  if n.id in self.nodes: raise ValueError("Duplicate node")
  self.nodes[n.id]=n
 def add_edge(self,s,t):
  if {"source":s,"target":t} not in self.edges:self.edges.append({"source":s,"target":t})
 def topological_sort(self):
  inc={n:0 for n in self.nodes}
  for e in self.edges:inc[e["target"]]+=1
  q=sorted(n for n,v in inc.items() if not v);out=[]
  while q:
   n=q.pop(0);out.append(n)
   for e in sorted((x for x in self.edges if x["source"]==n),key=lambda x:x["target"]):
    inc[e["target"]]-=1
    if not inc[e["target"]]:q.append(e["target"]);q.sort()
  if len(out)!=len(self.nodes):raise ValueError("Workflow graph contains a cycle.")
  return out
 def is_dag(self):
  try:self.topological_sort();return True
  except ValueError:return False
