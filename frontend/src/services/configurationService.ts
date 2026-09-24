import api from "./api";
import type {
  AnalysisConfiguration,
  BusinessObjective,
  ConfigurationPayload,
  TargetCandidate,
} from "../types/configuration";

export async function getBusinessObjectives(): Promise<BusinessObjective[]> {
  return (await api.get<{ success: boolean; objectives: BusinessObjective[] }>("/configuration/objectives")).data.objectives;
}

export async function getTargetCandidates(datasetId: string): Promise<TargetCandidate[]> {
  return (await api.get<{ success: boolean; candidates: TargetCandidate[] }>(`/datasets/${encodeURIComponent(datasetId)}/target-candidates`)).data.candidates;
}

export async function saveConfiguration(datasetId: string, payload: ConfigurationPayload): Promise<AnalysisConfiguration> {
  return (await api.post<{ success: boolean; configuration: AnalysisConfiguration }>(`/datasets/${encodeURIComponent(datasetId)}/configuration`, payload)).data.configuration;
}

export async function getConfiguration(datasetId: string): Promise<AnalysisConfiguration> {
  return (await api.get<{ success: boolean; configuration: AnalysisConfiguration }>(`/datasets/${encodeURIComponent(datasetId)}/configuration`)).data.configuration;
}
