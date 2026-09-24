from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class CapabilityDefinition:
    id: str
    label: str
    description: str
    category: str

CAPABILITIES = [
    CapabilityDefinition("missing_value_handling", "Missing Value Handling", "Assess the need to handle missing values.", "data_quality"),
    CapabilityDefinition("duplicate_handling", "Duplicate Handling", "Assess duplicate-row handling need.", "data_quality"),
    CapabilityDefinition("outlier_analysis", "Outlier Analysis", "Assess numerical outlier analysis need.", "analysis"),
    CapabilityDefinition("encoding", "Categorical Encoding", "Assess categorical feature encoding need.", "preprocessing"),
    CapabilityDefinition("scaling", "Feature Scaling", "Assess feature scaling need.", "preprocessing"),
    CapabilityDefinition("feature_selection", "Feature Selection", "Assess feature filtering need.", "feature_engineering"),
    CapabilityDefinition("imbalance_handling", "Class Imbalance Handling", "Assess classification target imbalance.", "data_quality"),
    CapabilityDefinition("text_analysis", "Text Analysis", "Assess free-form text analysis need.", "analysis"),
    CapabilityDefinition("temporal_analysis", "Temporal Analysis", "Assess datetime-aware analysis need.", "analysis"),
    CapabilityDefinition("dimensionality_reduction", "Dimensionality Reduction", "Assess dimensionality-reduction need.", "feature_engineering"),
    CapabilityDefinition("clustering", "Clustering", "Assess clustering workflow relevance.", "ml"),
    CapabilityDefinition("classification", "Classification", "Assess classification workflow relevance.", "ml"),
    CapabilityDefinition("regression", "Regression", "Assess regression workflow relevance.", "ml"),
    CapabilityDefinition("explainability", "Explainability", "Assess explanation requirements.", "explainability"),
    CapabilityDefinition("business_prioritization", "Business Prioritization", "Assess business prioritization relevance.", "business"),
]

def registry_as_dicts() -> list[dict[str, str]]:
    return [asdict(capability) for capability in CAPABILITIES]
