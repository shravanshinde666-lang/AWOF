from awof.awga import AWGAGenerator
from ..database import repository
from .dataset_service import get_profile
from .configuration_service import get_saved_configuration, ConfigurationNotFoundError
from .capability_service import get_capabilities, CapabilityResultNotFoundError
class WorkflowNotFoundError(Exception): pass
def generate_workflow(dataset_id):
 result=AWGAGenerator(get_profile(dataset_id),get_saved_configuration(dataset_id),get_capabilities(dataset_id)).generate()
 repository.save_stage(dataset_id,"workflow",result);return result
def get_workflow(dataset_id):
 try:return repository.get_stage(dataset_id,"workflow")
 except repository.PersistenceNotFoundError as exc:raise WorkflowNotFoundError("Adaptive workflow has not been generated.") from exc
