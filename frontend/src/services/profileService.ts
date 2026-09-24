import api from "./api";
import type { DatasetProfile } from "../types/profile";

function profilePath(datasetId: string): string {
  return `/datasets/${encodeURIComponent(datasetId)}/profile`;
}

/** Generate a fresh, aggregated intelligence profile for an uploaded dataset. */
export async function generateProfile(datasetId: string): Promise<DatasetProfile> {
  return (await api.post<DatasetProfile>(profilePath(datasetId))).data;
}

/** Retrieve the most recently generated in-memory profile for an uploaded dataset. */
export async function getProfile(datasetId: string): Promise<DatasetProfile> {
  return (await api.get<DatasetProfile>(profilePath(datasetId))).data;
}
