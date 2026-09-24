import unittest
import pandas as pd
from awof.execution.executor import execute
from awof.pruning import prune

class ExecutionTests(unittest.TestCase):
 def workflow(self,nodes):return {"workflow_id":"w","nodes":[{"id":x,"status":"selected"} for x in ["dataset_input","profile",*nodes,"output"]]}
 def test_duplicate_and_missing(self):
  df=pd.DataFrame({"x":[1,None,1],"cat":["a",None,"a"],"target":["y",None,"y"]});p=prune(self.workflow(["duplicate_handling","missing_values"]),df,"target","classification");r=execute(p,df,"d","target","classification","x");self.assertEqual(r["summary"]["final_rows"],2)
 def test_encoding_scaling_selection_pca(self):
  df=pd.DataFrame({"id":[1,2,3,4],"cat":["a","b","a","b"],"x":[1,2,3,4],"y":[2,4,6,8],"constant":[1]*4,"target":["a","b","a","b"]});p=prune(self.workflow(["encoding","scaling","feature_selection","dimensionality_reduction"]),df,"target","clustering");r=execute(p,df,"d","target","clustering","x");self.assertFalse(r["errors"])
