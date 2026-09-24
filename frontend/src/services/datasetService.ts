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
