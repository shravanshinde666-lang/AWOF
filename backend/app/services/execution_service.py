from awof.pruning import prune
from awof.execution.executor import execute
from .workflow_service import get_workflow
from .dataset_service import load_dataset_dataframe
from .configuration_service import get_saved_configuration
from ..database import repository
def prune_workflow(dataset_id):
 c=get_saved_configuration(dataset_id);p=prune(get_workflow(dataset_id),load_dataset_dataframe(dataset_id),(c.get("target")or{}).get("column"),c["problem_type"]);repository.save_stage(dataset_id,"pruned_workflow",p);return p
def get_pruned(dataset_id):
 try:return repository.get_stage(dataset_id,"pruned_workflow")
 except repository.PersistenceNotFoundError as exc:raise KeyError("Workflow has not been pruned.") from exc
def execute_workflow(dataset_id):
 c=get_saved_configuration(dataset_id);p=get_pruned(dataset_id);r=execute(p,load_dataset_dataframe(dataset_id),dataset_id,(c.get("target")or{}).get("column"),c["problem_type"],c["business_objective"]["id"]);repository.save_stage(dataset_id,"execution",r);return r
def get_execution(dataset_id):
 try:return repository.get_stage(dataset_id,"execution")
 except repository.PersistenceNotFoundError as exc:raise KeyError("Workflow has not been executed.") from exc
