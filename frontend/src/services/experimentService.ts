import api from "./api";
import type {
  ExperimentRequest,
  ExperimentSummary,
  ResearchExperimentResult,
} from "../types/experiment";

const datasetBase = (datasetId: string) =>
  `/datasets/${encodeURIComponent(datasetId)}/experiments`;

export const runComparison = (
  datasetId: string,
  runs: number,
  experimentName?: string,
) => {
  const payload: ExperimentRequest = {
    runs,
    ...(experimentName?.trim() ? { experiment_name: experimentName.trim() } : {}),
  };

  return api
    .post<ResearchExperimentResult>(`${datasetBase(datasetId)}/compare`, payload)
    .then((response) => response.data);
};

export const getExperiment = (experimentId: string) =>
  api
    .get<ResearchExperimentResult>(`/experiments/${encodeURIComponent(experimentId)}`)
    .then((response) => response.data);

export const getDatasetExperiments = (datasetId: string) =>
  api
    .get<ExperimentSummary[]>(datasetBase(datasetId))
    .then((response) => response.data);
