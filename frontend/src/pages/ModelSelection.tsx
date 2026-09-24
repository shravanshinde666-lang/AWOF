import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ModelRecommendation from "../components/models/ModelRecommendation";
import { getRecommendations, recommendModels, trainModels } from "../services/modelService";
import type { AMRAResult } from "../types/model";

export default function ModelSelection() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<AMRAResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    if (!datasetId) return;
    void getRecommendations(datasetId).catch(() => recommendModels(datasetId)).then(setRecommendations).catch(() => setError("Recommendations are unavailable. Complete execution first."));
  }, [datasetId]);
  async function train() {
    if (!datasetId) return;
    setTraining(true); setError(null);
    try { await trainModels(datasetId); navigate(`/datasets/${datasetId}/evaluation`); }
    catch { setError("Recommended model training could not be completed."); }
    finally { setTraining(false); }
  }
  if (error) return <main className="page"><p className="error-message">{error}</p></main>;
  if (!recommendations) return <main className="page">Generating adaptive model recommendations...</main>;
  const recommended = recommendations.models.filter((model) => model.decision === "recommended");
  const other = recommendations.models.filter((model) => model.decision !== "recommended");
  return <main className="page"><h1>Adaptive Model Recommendation</h1><p>Problem Type: {recommendations.problem_type}</p><p>Models evaluated by AMRA: {recommendations.summary.models_evaluated} · Models recommended: {recommendations.summary.models_recommended}</p><p>AMRA score is a pre-training suitability estimate; observed evaluation metrics are shown separately after training.</p><h2>Recommended Models</h2>{recommended.map((model) => <ModelRecommendation key={model.model_id} model={model} />)}<button type="button" onClick={train} disabled={training}>{training ? "Training recommended models..." : "Train Recommended Models"}</button><h2>Not Selected by AMRA</h2>{other.map((model) => <ModelRecommendation key={model.model_id} model={model} />)}</main>;
}
