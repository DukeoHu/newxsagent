import type {
  BibleSectionData,
  BibleSectionName,
  OnboardingDraftResponse,
  OnboardingQuestionResponse,
  OnboardingSession,
  Chapter,
  ChapterSummary,
  CreateProjectRequest,
  ExploreRecord,
  JobRecord,
  JobSubmitResponse,
  LLMConfig,
  LLMLogEntry,
  OutlineBundle,
  OutlineGenerateResult,
  ChapterBlueprintRecommendation,
  Project,
  ProjectStatus,
  SupervisionResponse,
  WriteChapterRequest,
  VolumeWriteRequest,
} from "./types";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/api/projects"),

  createProject: (body: CreateProjectRequest) =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getProjectStatus: (projectId: string) =>
    request<ProjectStatus>(`/api/projects/${projectId}/status`),

  deleteProject: (projectId: string) =>
    request<void>(`/api/projects/${projectId}`, {
      method: "DELETE",
    }),

  getSupervision: (projectId: string) =>
    request<SupervisionResponse>(`/api/projects/${projectId}/supervision`),

  listLLMLogs: (projectId: string, limit = 50) =>
    request<LLMLogEntry[]>(`/api/projects/${projectId}/logs/llm?limit=${limit}`),

  resolveSupervision: (
    projectId: string,
    body: {
      pending_id: string;
      action: "apply" | "ignore" | "rollback";
      actor?: string;
    },
  ) =>
    request<{ ok: boolean }>(`/api/projects/${projectId}/supervision/resolve`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  writeChapter: (projectId: string, body: WriteChapterRequest) =>
    request<JobSubmitResponse>(`/api/projects/${projectId}/jobs/write-chapter`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  writeVolume: (projectId: string, body: VolumeWriteRequest) =>
    request<JobSubmitResponse>(`/api/projects/${projectId}/jobs/write-volume`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getJob: (projectId: string, jobId: string) =>
    request<JobRecord>(`/api/projects/${projectId}/jobs/${jobId}`),

  getChapter: (projectId: string, chapterId: string) =>
    request<Chapter>(`/api/projects/${projectId}/chapters/${chapterId}`),

  listChapters: (projectId: string) =>
    request<ChapterSummary[]>(`/api/projects/${projectId}/chapters`),

  deleteChapter: (projectId: string, chapterId: string) =>
    request<void>(`/api/projects/${projectId}/chapters/${chapterId}`, {
      method: "DELETE",
    }),

  listBibleSections: (projectId: string) =>
    request<BibleSectionName[]>(`/api/projects/${projectId}/bible/sections`),

  getBibleSection: (projectId: string, section: BibleSectionName) =>
    request<BibleSectionData>(`/api/projects/${projectId}/bible/${section}`),

  putBibleSection: (
    projectId: string,
    section: BibleSectionName,
    data: Record<string, unknown>,
  ) =>
    request<BibleSectionData>(`/api/projects/${projectId}/bible/${section}`, {
      method: "PUT",
      body: JSON.stringify({ data }),
    }),

  generateOnboarding: (projectId: string) =>
    request<OnboardingDraftResponse>(`/api/projects/${projectId}/onboarding`, {
      method: "POST",
    }),

  getOnboardingSession: (projectId: string) =>
    request<OnboardingSession | null>(
      `/api/projects/${projectId}/onboarding/session`,
    ),

  startOnboarding: (projectId: string) =>
    request<OnboardingQuestionResponse>(
      `/api/projects/${projectId}/onboarding/start`,
      { method: "POST" },
    ),

  answerOnboarding: (projectId: string, answer: string) =>
    request<OnboardingQuestionResponse>(
      `/api/projects/${projectId}/onboarding/answer`,
      {
        method: "POST",
        body: JSON.stringify({ answer }),
      },
    ),

  applyOnboarding: (
    projectId: string,
    draft: Partial<Record<BibleSectionName, BibleSectionData>>,
  ) =>
    request<{ ok: boolean }>(`/api/projects/${projectId}/onboarding/apply`, {
      method: "POST",
      body: JSON.stringify({ bible: draft }),
    }),

  clearOnboardingDraft: (projectId: string) =>
    request<OnboardingSession>(
      `/api/projects/${projectId}/onboarding/clear-draft`,
      { method: "POST" },
    ),

  getOutlines: (projectId: string) =>
    request<OutlineBundle>(`/api/projects/${projectId}/outlines`),

  generateMasterOutline: (projectId: string) =>
    request<Record<string, unknown>>(
      `/api/projects/${projectId}/outlines/generate-master`,
      { method: "POST" },
    ),

  generateNarrativeThreads: (
    projectId: string,
    body?: { only_missing?: boolean; apply?: boolean },
  ) =>
    request<{
      volumes: Array<{ volume_id: string; threads: unknown[] }>;
      applied: number;
      skipped: number;
    }>(`/api/projects/${projectId}/outlines/generate-threads`, {
      method: "POST",
      body: JSON.stringify(body ?? { only_missing: true, apply: true }),
    }),

  generateOutlines: (
    projectId: string,
    body: {
      scope: "all" | "volume" | "chapters";
      volume_id?: string;
      chapter_ids?: string[];
      only_pending?: boolean;
      apply?: boolean;
      regenerate_master?: boolean;
    },
  ) =>
    request<OutlineGenerateResult>(
      `/api/projects/${projectId}/outlines/generate`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    ),

  generateChapterBlueprint: (projectId: string, chapterId: string) =>
    request<ChapterBlueprintRecommendation>(
      `/api/projects/${projectId}/outlines/chapters/${chapterId}/generate`,
      { method: "POST" },
    ),

  putChapterBlueprint: (
    projectId: string,
    chapterId: string,
    body: {
      chapter_id: string;
      title: string;
      beats: string[];
      constraints?: string[];
      hard_constraints?: Record<string, unknown>;
      author_notes?: string;
      chapter_role?: string;
      primary_thread?: string;
      dormant_threads?: string[];
      status: string;
    },
  ) =>
    request(`/api/projects/${projectId}/outlines/chapters/${chapterId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  putVolumeOutline: (
    projectId: string,
    volumeId: string,
    body: {
      volume_id?: string;
      title: string;
      arcs: Array<Record<string, unknown>>;
      chapter_range: number[];
    },
  ) =>
    request(`/api/projects/${projectId}/outlines/volumes/${volumeId}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  putMasterOutline: (
    projectId: string,
    body: { acts?: Array<Record<string, unknown>>; themes?: string[] },
  ) =>
    request(`/api/projects/${projectId}/outlines/master`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  getLLMConfig: () => request<LLMConfig>("/api/settings/llm"),

  updateLLMConfig: (body: LLMConfig) =>
    request<LLMConfig>("/api/settings/llm", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  createExplore: (
    projectId: string,
    body: { chapter_id?: string; prompt: string; count?: number },
  ) =>
    request<ExploreRecord>(`/api/projects/${projectId}/explore`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  adoptExplore: (
    projectId: string,
    exploreId: string,
    body: { option_id: string; actor?: string },
  ) =>
    request<{ ok: boolean }>(`/api/projects/${projectId}/explore/${exploreId}/adopt`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  runDream: (projectId: string) =>
    request<{
      orphan_summaries_removed: string[];
      duplicate_rules_removed: number;
      notes_updated: boolean;
    }>(`/api/projects/${projectId}/maintenance/dream`, { method: "POST" }),

  runDistill: (projectId: string) =>
    request<{ added_rules: unknown[]; skipped_existing: number; source_decisions: number }>(
      `/api/projects/${projectId}/maintenance/distill`,
      { method: "POST" },
    ),
};

export function subscribeJobEvents(
  projectId: string,
  jobId: string,
  onEvent: (event: { type: string; data: Record<string, unknown> }) => void,
  onError?: (err: Error) => void,
): () => void {
  const source = new EventSource(
    `/api/projects/${projectId}/jobs/${jobId}/events`,
  );

  const handlers: Record<string, (e: MessageEvent) => void> = {};

  const attach = (type: string) => {
    handlers[type] = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as Record<string, unknown>;
        onEvent({ type, data });
      } catch (err) {
        onError?.(err instanceof Error ? err : new Error(String(err)));
      }
    };
    source.addEventListener(type, handlers[type]);
  };

  [
    "job.progress",
    "job.chunk",
    "job.complete",
    "job.error",
    "message",
  ].forEach(attach);

  source.onerror = () => {
    onError?.(new Error("SSE connection error"));
  };

  return () => {
    Object.entries(handlers).forEach(([type, handler]) => {
      source.removeEventListener(type, handler);
    });
    source.close();
  };
}

export { ApiError };
