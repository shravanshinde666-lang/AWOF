import api from "./api";
import type { ACSAResult } from "../types/capability";

const path = (datasetId: string) => `/datasets/${encodeURIComponent(datasetId)}/capabilities`;
export async function generateCapabilities(datasetId: string): Promise<ACSAResult> {
  return (await api.post<ACSAResult>(path(datasetId))).data;
}
export async function getCapabilities(datasetId: string): Promise<ACSAResult> {
  return (await api.get<ACSAResult>(path(datasetId))).data;
}
