import { BrowserRouter, Route, Routes } from "react-router-dom";

import ErrorBoundary from "./components/common/ErrorBoundary";
import Navbar from "./components/common/Navbar";
import DatasetIntelligence from "./pages/DatasetIntelligence";
import ConfigureAnalysis from "./pages/ConfigureAnalysis";
import CapabilityScores from "./pages/CapabilityScores";
import Workflow from "./pages/Workflow";
import Execution from "./pages/Execution";
import ModelSelection from "./pages/ModelSelection";
import Evaluation from "./pages/Evaluation";
import Explainability from "./pages/Explainability";
import BusinessIntelligence from "./pages/BusinessIntelligence";
import ResearchComparison from "./pages/ResearchComparison";
import Home from "./pages/Home";
import UploadDataset from "./pages/UploadDataset";

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="app-shell">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<UploadDataset />} />
            <Route path="/datasets/:datasetId/intelligence" element={<DatasetIntelligence />} />
            <Route path="/datasets/:datasetId/configure" element={<ConfigureAnalysis />} />
            <Route path="/datasets/:datasetId/capabilities" element={<CapabilityScores />} />
            <Route path="/datasets/:datasetId/workflow" element={<Workflow />} />
            <Route path="/datasets/:datasetId/execution" element={<Execution />} />
            <Route path="/datasets/:datasetId/models" element={<ModelSelection />} />
            <Route path="/datasets/:datasetId/evaluation" element={<Evaluation />} />
            <Route path="/datasets/:datasetId/explainability" element={<Explainability />} />
            <Route path="/datasets/:datasetId/business" element={<BusinessIntelligence />} />
            <Route path="/datasets/:datasetId/research" element={<ResearchComparison />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
