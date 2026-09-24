from typing import Any

from awof.configuration.configuration import build_configuration
from awof.configuration.objectives import list_objectives
from awof.configuration.target_analyzer import analyze_target_candidates

from ..database import repository
from .dataset_service import DatasetNotFoundError, get_profile


class ConfigurationNotFoundError(Exception):
    pass


class ConfigurationValidationError(Exception):
    def __init__(self, configuration: dict[str, Any]) -> None:
        super().__init__("Analysis configuration is invalid.")
        self.configuration = configuration


def list_business_objectives() -> list[dict[str, Any]]:
    return list_objectives()


def get_target_candidates(dataset_id: str) -> list[dict[str, Any]]:
    profile = get_profile(dataset_id)
    return analyze_target_candidates(profile)


def validate_configuration(
    dataset_id: str,
    business_objective: str,
    target_column: str | None,
) -> dict[str, Any]:
    profile = get_profile(dataset_id)
    return build_configuration(dataset_id, business_objective, target_column, profile)


def save_configuration(
    dataset_id: str,
    business_objective: str,
    target_column: str | None,
) -> dict[str, Any]:
    configuration = validate_configuration(dataset_id, business_objective, target_column)
    if not configuration["valid"]:
        raise ConfigurationValidationError(configuration)
    repository.save_stage(dataset_id, "configuration", configuration)
    return configuration


def get_saved_configuration(dataset_id: str) -> dict[str, Any]:
    try:
        return repository.get_stage(dataset_id, "configuration")
    except repository.PersistenceNotFoundError as exc:
        raise ConfigurationNotFoundError("Analysis configuration has not been saved.") from exc
