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
export interface VisualInsights {target:string|null;problem_type:string|null;positive_class:string|null;target_distribution:Array<{label:string;count:number;percentage:number}>;category_target_rates:Array<{feature:string;values:Array<{category:string;rate:number;count:number}>}>;correlation_matrix:{columns:string[];values:Array<Array<number|null>>}|null;feature_target_ranking:{method:string;items:Array<{feature:string;score:number}>;message:string|null}}
export const getVisualInsights=(datasetId:string)=>api.get<VisualInsights>(`/datasets/${encodeURIComponent(datasetId)}/insights`).then(response=>response.data);
