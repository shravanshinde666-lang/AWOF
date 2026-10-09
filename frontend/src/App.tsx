import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import ErrorBoundary from "./components/common/ErrorBoundary";
import Navbar from "./components/common/Navbar";
import Sidebar from "./components/common/Sidebar";

const Home = lazy(() => import("./pages/Home"));
const UploadDataset = lazy(() => import("./pages/UploadDataset"));
const DatasetIntelligence = lazy(() => import("./pages/DatasetIntelligence"));
const ConfigureAnalysis = lazy(() => import("./pages/ConfigureAnalysis"));
const CapabilityScores = lazy(() => import("./pages/CapabilityScores"));
const Workflow = lazy(() => import("./pages/Workflow"));
const Execution = lazy(() => import("./pages/Execution"));
const ModelSelection = lazy(() => import("./pages/ModelSelection"));
const Evaluation = lazy(() => import("./pages/Evaluation"));
const Explainability = lazy(() => import("./pages/Explainability"));
const BusinessIntelligence = lazy(() => import("./pages/BusinessIntelligence"));
const ResearchComparison = lazy(() => import("./pages/ResearchComparison"));
const Report = lazy(() => import("./pages/Report"));
const ProjectHistory = lazy(() => import("./pages/ProjectHistory"));

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="app-shell">
          <Sidebar />
          <div className="app-content">
            <Navbar />
            <Suspense fallback={<main className="page route-loading" role="status">Loading workspace...</main>}>
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
            <Route path="/datasets/:datasetId/report" element={<Report />} />
            <Route path="/datasets/:datasetId/history" element={<ProjectHistory />} />
              </Routes>
            </Suspense>
          </div>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
