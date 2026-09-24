import unittest
import pandas as pd
from awof.pruning import prune
class PruningTests(unittest.TestCase):
 def test_prunes_clean_nodes(self):
  w={"workflow_id":"w","nodes":[{"id":x,"status":"selected"} for x in ["dataset_input","profile","missing_values","duplicate_handling","encoding","dimensionality_reduction","output"]]}
  r=prune(w,pd.DataFrame({"x":[1,2]}),None,"classification");ids=[n["id"] for n in r["nodes"]];self.assertIn("dataset_input",ids);self.assertNotIn("missing_values",ids);self.assertNotIn("encoding",ids)
