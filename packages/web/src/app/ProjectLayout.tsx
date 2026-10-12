import { Outlet, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { AppShell } from "../components/layout/AppShell";

export function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: status } = useQuery({
    queryKey: ["project-status", projectId],
    queryFn: () => api.getProjectStatus(projectId!),
    enabled: !!projectId,
  });

  if (!projectId) return null;

  return (
    <AppShell
      projectId={projectId}
      projectTitle={status?.name}
      onboardingComplete={status?.onboarding_complete}
      showSupervision
    >
      <Outlet />
    </AppShell>
  );
}
