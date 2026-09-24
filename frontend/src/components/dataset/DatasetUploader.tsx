import { type ChangeEvent, type DragEvent, useState } from "react";
import { AxiosError } from "axios";
import { type DatasetMetadata, uploadDataset } from "../../services/datasetService";

interface Props { onUploaded: (dataset: DatasetMetadata) => void; }
const maxSize = 50 * 1024 * 1024;

export default function DatasetUploader({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const select = (next?: File) => {
    setError(null); setMessage(null);
    if (!next) return;
    if (!["csv", "xlsx", "xls"].includes(next.name.split(".").pop()?.toLowerCase() ?? "")) {
      setFile(null); setError("Only CSV and Excel files are supported."); return;
    }
    if (next.size > maxSize) { setFile(null); setError("File exceeds the maximum allowed size."); return; }
    setFile(next);
  };
  const upload = async () => {
    if (!file) { setError("Select a CSV or Excel file before uploading."); return; }
    setUploading(true); setError(null); setMessage(null);
    try { const result = await uploadDataset(file); onUploaded(result.dataset); setMessage(result.message); }
    catch (cause) {
      const response = cause instanceof AxiosError ? cause.response?.data as { error?: string } : undefined;
      setError(
        response?.error
        ?? (cause instanceof AxiosError && !cause.response
          ? "Cannot reach the API. Confirm the backend is running, then retry."
          : "Unable to upload the dataset."),
      );
    } finally { setUploading(false); }
  };
  return <section className="uploader">
    <label className="drop-zone" htmlFor="dataset-file" onDragOver={(event) => event.preventDefault()} onDrop={(event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); select(event.dataTransfer.files[0]); }}>
      Select or drop a dataset file
      <input id="dataset-file" type="file" accept=".csv,.xlsx,.xls" onChange={(event: ChangeEvent<HTMLInputElement>) => select(event.target.files?.[0])} />
    </label>
    {file && <p>Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>}
    <button type="button" onClick={upload} disabled={!file || uploading}>{uploading ? "Uploading dataset..." : "Upload Dataset"}</button>
    {message && <p className="success-message">{message}</p>}
    {error && <p className="error-message" role="alert">{error}</p>}
  </section>;
}
