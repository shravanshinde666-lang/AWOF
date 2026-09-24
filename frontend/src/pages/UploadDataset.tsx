import { AxiosError } from "axios";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DatasetPreview from "../components/dataset/DatasetPreview";
import DatasetSummary from "../components/dataset/DatasetSummary";
import DatasetUploader from "../components/dataset/DatasetUploader";
import { type DatasetMetadata } from "../services/datasetService";
import { generateProfile } from "../services/profileService";

export default function UploadDataset() {
  const [dataset, setDataset] = useState<DatasetMetadata | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const navigate = useNavigate();

  const analyzeDataset = async () => {
    if (!dataset) return;
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      await generateProfile(dataset.dataset_id);
      navigate(`/datasets/${encodeURIComponent(dataset.dataset_id)}/intelligence`);
    } catch (cause) {
      const response = cause instanceof AxiosError
        ? (cause.response?.data as { error?: string; detail?: string } | undefined)
        : undefined;
      setAnalysisError(response?.error ?? response?.detail ?? "Unable to analyze this dataset. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <main className="page">
      <header className="page-hero">
        <p className="eyebrow">NEW ANALYSIS</p>
        <h1>Bring your dataset to life.</h1>
        <p>Upload a CSV or Excel file. AWOF will inspect it first, then shape an adaptive analytics workflow around its actual structure.</p>
      </header>
      <DatasetUploader onUploaded={(uploadedDataset) => {
        setDataset(uploadedDataset);
        setAnalysisError(null);
      }} />
      <div className="upload-rules"><span>CSV, XLSX, XLS</span><span>Up to 50 MB</span><span>Stored safely per project</span></div>
      {dataset && (
        <div className="dataset-results">
          <DatasetSummary dataset={dataset} />
          <DatasetPreview dataset={dataset} />
          <section className="analysis-action" aria-labelledby="analyze-heading">
            <h2 id="analyze-heading">Ready for dataset intelligence?</h2>
            <p>Generate an aggregated profile with type detection, quality signals, statistics, outlier detection, correlations, and distributions.</p>
            <button type="button" onClick={() => void analyzeDataset()} disabled={analyzing}>
              {analyzing ? "Analyzing dataset..." : "Analyze Dataset"}
            </button>
            {analysisError && <p className="error-message" role="alert">{analysisError}</p>}
          </section>
        </div>
      )}
    </main>
  );
}
