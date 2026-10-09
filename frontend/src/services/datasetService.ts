import api from "./api";

export interface DatasetMetadata {
  dataset_id: string;
  original_filename: string;
  stored_filename: string;
  file_type: string;
  file_size_bytes: number;
  rows: number;
  columns: number;
  column_names: string[];
  preview: Record<string, unknown>[];
  sheet_name?: string | null;
}

export interface DatasetUploadResponse { success: boolean; message: string; dataset: DatasetMetadata; }
export interface DatasetPreviewResponse { success: boolean; dataset_id: string; rows: Record<string, unknown>[]; }
export interface StageHistoryItem { stage: string; updated_at: string; }
export interface DatasetSummaryResponse { dataset: DatasetMetadata; stages: StageHistoryItem[]; }
export interface DatasetHistoryResponse { dataset_id: string; stages: StageHistoryItem[]; }
export interface FinalReportResponse {
  dataset: DatasetMetadata;
  stages: Record<string, unknown>;
  research: unknown;
  limitations: string[];
}

export async function uploadDataset(file: File): Promise<DatasetUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  // Do not set Content-Type manually: the browser supplies the multipart
  // boundary required by FastAPI when it receives FormData.
  return (await api.post<DatasetUploadResponse>("/datasets/upload", form)).data;
}
export async function getDataset(datasetId: string): Promise<DatasetMetadata> {
  return (await api.get<DatasetMetadata>(`/datasets/${datasetId}`)).data;
}
export async function getDatasetPreview(datasetId: string, limit = 10): Promise<DatasetPreviewResponse> {
  return (await api.get<DatasetPreviewResponse>(`/datasets/${datasetId}/preview`, { params: { limit } })).data;
}
export const listDatasets = () => api.get<DatasetMetadata[]>("/datasets").then(response => response.data);
export const getDatasetSummary = (datasetId: string) => api.get<DatasetSummaryResponse>(`/datasets/${datasetId}/summary`).then(response => response.data);
export const getDatasetHistory = (datasetId: string) => api.get<DatasetHistoryResponse>(`/datasets/${datasetId}/history`).then(response => response.data);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeStagePayload(value: unknown): unknown {
  if (!isRecord(value) || !isRecord(value.result)) return value;
  return { ...value.result, items: Array.isArray(value.items) ? value.items : value.result.items };
}

function normalizeFinalReport(report: FinalReportResponse): FinalReportResponse {
  return {
    ...report,
    stages: Object.fromEntries(
      Object.entries(report.stages).map(([stage, value]) => [stage, normalizeStagePayload(value)]),
    ),
  };
}

export const getFinalReport = (datasetId: string, compact = true) =>
  api.get<FinalReportResponse>(`/datasets/${datasetId}/report`, { params: { compact } })
    .then(response => normalizeFinalReport(response.data));
