def validate_graph(graph,problem_type):
 e=[];ids=set(graph.nodes)
 if not {"dataset_input","profile","output"}<=ids:e.append("Required core nodes are missing.")
 if any(x["source"] not in ids or x["target"] not in ids or x["source"]==x["target"] for x in graph.edges):e.append("Invalid edge.")
 dag=graph.is_dag()
 if not dag:e.append("Graph contains a cycle.")
 tasks={"classification","regression","clustering"}&ids
 if problem_type in tasks|{"classification","regression","clustering"} and tasks!={problem_type}:e.append("Workflow task does not match configuration.")
 return {"valid":not e,"is_dag":dag,"errors":e,"warnings":[]}
