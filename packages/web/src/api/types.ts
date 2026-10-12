export interface Project {
  id: string;
  name: string;
  genre: string;
  intervention_level: string;
  created_at: string;
  updated_at: string;
  path: string;
}

export interface HealthScore {
  overall: number;
  session: number;
  pending_count: number;
}

export interface ProjectStatus {
  project_id: string;
  name: string;
  health: HealthScore;
  chapter_count: number;
  onboarding_complete: boolean;
  summary: Record<string, unknown>;
}

export interface CreateProjectRequest {
  name: string;
  genre?: string;
  intervention_level?: string;
}

export interface PendingItem {
  id: string;
  project_id: string;
  item_type: string;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "resolved" | "ignored";
  summary: string;
  created_at: string;
}

export interface ActionLogEntry {
  timestamp: string;
  action_type: string;
  diff_summary: string;
  rollback_ref?: string | null;
  metadata?: Record<string, unknown>;
}

export interface LLMLogEntry {
  id: string;
  timestamp: string;
  project_id?: string | null;
  job_id?: string | null;
  task: string;
  llm_mode: string;
  model: string;
  system: string;
  prompt: string;
  json_mode: boolean;
  response?: string | null;
  error?: string | null;
  latency_ms: number;
  status: string;
  system_truncated: boolean;
  prompt_truncated: boolean;
  response_truncated: boolean;
  metadata?: Record<string, unknown>;
}

export interface SupervisionHealth {
  overall: number;
  session: number;
  pending_count: number;
  base_overall: number;
  base_session: number;
}

export interface SupervisionResponse {
  health: SupervisionHealth;
  pending_items: PendingItem[];
  recent_actions: ActionLogEntry[];
  quick_links: Record<string, string>;
}

export interface WriteChapterRequest {
  instruction?: string;
  chapter_id?: string;
  max_mode?: boolean | null;
}

export interface VolumeWriteRequest {
  instruction?: string;
  volume_id?: string;
  limit?: number;
  max_mode?: boolean | null;
  stop_on_revision?: boolean;
}

export interface JobSubmitResponse {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
}

export interface WriteChapterResult {
  job_id: string;
  status: string;
  chapter_id: string;
  word_count: number;
  drift_findings_count: number;
  pending_ids: string[];
  compacted: boolean;
  actions_logged: string[];
  goal_satisfied?: boolean;
  goal_impossible?: boolean;
  goal_summary?: string;
  blueprint_status?: string;
  rewrite_count?: number;
  checkpointed?: boolean;
  kind?: "chapter";
  max_mode_used?: boolean;
  selected_plan?: string;
}

export interface VolumeWriteResult {
  kind: "volume";
  job_id: string;
  status: string;
  volume_id?: string | null;
  chapters_attempted: string[];
  chapters_completed: string[];
  stopped_reason: string;
  chapter_results: WriteChapterResult[];
  goal_satisfied: boolean;
}

export interface JobEvent {
  type: string;
  data: Record<string, unknown>;
  ts: number;
}

export interface JobRecord {
  id: string;
  project_id: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  job_type?: string;
  result?: WriteChapterResult | VolumeWriteResult | null;
  error?: string | null;
  events: JobEvent[];
}

export interface ChapterSummary {
  id: string;
  title: string;
  word_count: number;
  filename: string;
}

export interface Chapter {
  id: string;
  title: string;
  content_md: string;
  word_count: number;
  filename: string;
}

export type BibleSectionName =
  | "characters"
  | "plot"
  | "timeline"
  | "world"
  | "notes";

export interface CharacterItem {
  name?: string;
  role?: string;
  goal?: string;
  arc?: string;
  description?: string;
  [key: string]: unknown;
}

export interface PlotSection {
  acts: Array<Record<string, unknown>>;
  themes: string[];
  locked_fields: string[];
}

export interface TimelineSection {
  events: Array<Record<string, unknown>>;
  locked_fields: string[];
}

export interface WorldSection {
  rules: Array<Record<string, unknown>>;
  locations: Array<Record<string, unknown>>;
  locked_fields: string[];
}

export interface StyleRuleItem {
  id: string;
  category:
    | "perspective"
    | "tone"
    | "pacing"
    | "dialogue"
    | "diction"
    | "technique"
    | "taboo"
    | string;
  title: string;
  description: string;
  priority: "must" | "should" | "prefer" | string;
}

export interface NotesSection {
  style_notes: string;
  style_rules?: StyleRuleItem[];
  author_notes: string;
  spoiler_vault?: string;
  locked_fields: string[];
}

export interface CharactersSection {
  characters: CharacterItem[];
  locked_fields: string[];
}

export type BibleSectionData =
  | CharactersSection
  | PlotSection
  | TimelineSection
  | WorldSection
  | NotesSection;

export interface OnboardingTurn {
  role: "assistant" | "user";
  content: string;
  question_id?: string | null;
}

export interface OnboardingSession {
  session_id: string;
  project_id: string;
  status: "active" | "ready" | "applied";
  started_at: string;
  updated_at: string;
  turns: OnboardingTurn[];
  context: Record<string, unknown>;
  draft?: Partial<Record<BibleSectionName, BibleSectionData>> | null;
}

export interface OnboardingQuestionResponse {
  session: OnboardingSession;
  question?: string | null;
  question_id?: string | null;
  ready_to_generate: boolean;
  hint?: string | null;
}

export interface OnboardingDraftResponse {
  project_id: string;
  draft: Partial<Record<BibleSectionName, BibleSectionData>>;
  llm_mode: "simulator" | "ollama" | "deepseek";
  warning?: string | null;
}

export interface LLMConfig {
  mode: "simulator" | "ollama" | "deepseek";
  ollama_base_url: string;
  ollama_model: string;
  ollama_think: boolean;
  strip_think_tags: boolean;
  deepseek_base_url: string;
  deepseek_api_key: string;
  deepseek_model: string;
  deepseek_reasoning_effort: string;
  deepseek_thinking_enabled: boolean;
}

export interface MasterOutline {
  acts: Array<Record<string, unknown>>;
  themes: string[];
  ending_goal?: string;
  completion: number;
}

export interface ChapterBlueprintRecommendation {
  chapter_id: string;
  title: string;
  beats: string[];
  constraints: string[];
  hard_constraints?: Record<string, unknown>;
  author_notes?: string;
  chapter_role?: string;
  primary_thread?: string;
  dormant_threads?: string[];
  status: string;
}

export interface OutlineGenerateResult {
  chapters?: ChapterBlueprintRecommendation[];
  applied?: number;
  master?: Record<string, unknown>;
  volumes?: Array<{ volume_id: string; applied: number }>;
}

export interface NarrativeThreadStage {
  level: number;
  id: string;
  label: string;
  ceiling: string;
}

export interface NarrativeThreadMilestone {
  id: string;
  summary: string;
  earliest_chapter: number;
}

export interface NarrativeThread {
  id: string;
  label: string;
  priority_curve: string;
  milestones?: NarrativeThreadMilestone[];
  stages?: NarrativeThreadStage[];
}

export interface VolumeOutline {
  volume_id: string;
  title: string;
  arcs: Array<Record<string, unknown>>;
  arc_phases?: Array<Record<string, unknown>>;
  chapter_range: number[];
  stage_goal?: string;
  opening_focus?: string;
  threads?: NarrativeThread[];
  allowed_knowledge?: string[];
  opening_knowledge?: string[];
  forbidden_reveals?: string[];
  knowledge_ceiling?: string;
  foreshadowing_plants?: Array<Record<string, unknown>>;
}

export interface ChapterBlueprint {
  chapter_id: string;
  title: string;
  beats: string[];
  constraints: string[];
  hard_constraints?: Record<string, unknown>;
  author_notes?: string;
  chapter_role?: string;
  primary_thread?: string;
  dormant_threads?: string[];
  status: string;
}

export interface OutlineBundle {
  master: MasterOutline;
  volumes: VolumeOutline[];
  chapters: ChapterBlueprint[];
  completion: number;
}

export interface ExploreOption {
  option_id: string;
  chapter_id: string;
  title: string;
  summary: string;
  beats: string[];
  constraints: string[];
  risk_level: "low" | "medium" | "high";
}

export interface ExploreRecord {
  explore_id: string;
  project_id: string;
  chapter_id: string;
  prompt: string;
  created_at: string;
  options: ExploreOption[];
  recommended_option_id?: string | null;
  judge_reason?: string;
}
