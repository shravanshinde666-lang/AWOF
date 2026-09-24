import unittest
import pandas as pd
from awof.profiler import DatasetProfiler
from awof.configuration.configuration import build_configuration
from awof.acsa import ACSAScorer
from awof.awga import AWGAGenerator
from awof.awga.graph import WorkflowGraph
from awof.awga.node import WorkflowNode
from awof.awga.validator import validate_graph

class AWGATests(unittest.TestCase):
 def workflow(self,objective,target,df):
  profile=DatasetProfiler(df,dataset_id="x").generate_profile();config=build_configuration("x",objective,target,profile);acsa=ACSAScorer(profile,config,df).generate();return AWGAGenerator(profile,config,acsa).generate()
 def test_classification(self):
  w=self.workflow("analyze_retention","target",pd.DataFrame({"kind":["a","b","a"],"target":["n","y","n"]}));ids=set(w["execution_order"]);self.assertIn("classification",ids);self.assertNotIn("regression",ids);self.assertTrue(w["validation"]["is_dag"])
 def test_regression(self):
  w=self.workflow("predict_behavior","target",pd.DataFrame({"x":[1,2,3,4],"target":[1.1,2.3,3.8,4.4]}));self.assertIn("regression",w["execution_order"]);self.assertNotIn("classification",w["execution_order"])
 def test_clustering_and_optional_scaling(self):
  w=self.workflow("segment_customers",None,pd.DataFrame({"x":[1,2,3],"y":[10,20,30]}));self.assertIn("clustering",w["execution_order"]);self.assertNotIn("classification",w["execution_order"])
 def test_business_analysis_has_no_forced_model(self):
  w=self.workflow("optimize_revenue",None,pd.DataFrame({"revenue":[10,20,30],"month":[1,2,3]}));ids=set(w["execution_order"]);self.assertNotIn("classification",ids);self.assertNotIn("regression",ids);self.assertNotIn("clustering",ids)
 def test_cycle_rejected(self):
  g=WorkflowGraph()
  for x in ["dataset_input","profile","output"]:g.add_node(WorkflowNode(x,x,"x",None,"core",True))
  g.add_edge("dataset_input","profile");g.add_edge("profile","output");g.add_edge("output","dataset_input")
  self.assertFalse(validate_graph(g,"business_analysis")["valid"])
 def test_determinism(self):
  df=pd.DataFrame({"x":[1,2,3],"target":["a","b","a"]});a=self.workflow("predict_behavior","target",df);b=self.workflow("predict_behavior","target",df)
  for key in ["nodes","edges","execution_order","excluded_capabilities"]:self.assertEqual(a[key],b[key])
