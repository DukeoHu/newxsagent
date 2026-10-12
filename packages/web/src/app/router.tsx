import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ProjectLayout } from "./ProjectLayout";
import { HomePage } from "../pages/HomePage";
import { OverviewPage } from "../pages/OverviewPage";
import { WritePage } from "../pages/WritePage";
import { ComponentPreviewPage } from "../pages/ComponentPreviewPage";
import { BiblePage } from "../pages/BiblePage";
import { OnboardingPage } from "../pages/OnboardingPage";
import { ChaptersPage } from "../pages/ChaptersPage";
import { SupervisionPage } from "../pages/SupervisionPage";
import { LLMLogsPage } from "../pages/LLMLogsPage";
import { PlanningPage } from "../pages/PlanningPage";
import { QualityDashboardPage } from "../pages/QualityDashboardPage";
import { KnowledgeGraphPage } from "../pages/KnowledgeGraphPage";
import { LLMSettingsStandalonePage } from "../pages/LLMSettingsStandalonePage";
import { ExplorePage } from "../pages/ExplorePage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dev/components" element={<ComponentPreviewPage />} />
        <Route path="/settings/llm" element={<LLMSettingsStandalonePage />} />
        <Route path="/projects/:projectId" element={<ProjectLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="write" element={<WritePage />} />
          <Route path="bible" element={<BiblePage />} />
          <Route path="planning" element={<PlanningPage />} />
          <Route path="quality" element={<QualityDashboardPage />} />
          <Route path="knowledge" element={<KnowledgeGraphPage />} />
          <Route path="explore" element={<ExplorePage />} />
          <Route path="onboarding" element={<OnboardingPage />} />
          <Route path="chapters" element={<ChaptersPage />} />
          <Route path="supervision" element={<SupervisionPage />} />
          <Route path="llm-logs" element={<LLMLogsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
