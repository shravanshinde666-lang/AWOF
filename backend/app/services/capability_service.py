from typing import Any

from awof.acsa import ACSAScorer

from ..database import repository
from .configuration_service import ConfigurationNotFoundError, get_saved_configuration
from .dataset_service import DatasetNotFoundError, get_profile, load_dataset_dataframe

class CapabilityResultNotFoundError(Exception):
    pass

def generate_capabilities(dataset_id: str) -> dict[str, Any]:
    profile = get_profile(dataset_id)
    configuration = get_saved_configuration(dataset_id)
    if not configuration["valid"]:
        raise ValueError("Analysis configuration must be valid before capability scoring.")
    result = ACSAScorer(profile, configuration, load_dataset_dataframe(dataset_id)).generate()
    repository.save_stage(dataset_id, "capabilities", result)
    return result

def get_capabilities(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "capabilities")
    except repository.PersistenceNotFoundError as exc:
        raise CapabilityResultNotFoundError("Capability analysis has not been generated.") from exc
