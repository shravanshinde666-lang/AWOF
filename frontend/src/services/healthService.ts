import api from "./api";

export interface HealthResponse {
  status: string;
  backend: string;
  service: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}
