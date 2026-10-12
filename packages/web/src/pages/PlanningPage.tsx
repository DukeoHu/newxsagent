import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { api } from "../api/client";
import type {
  ChapterBlueprint,
  ChapterBlueprintRecommendation,
  NarrativeThread,
  VolumeOutline,
} from "../api/types";
import {
  SCALE_APPLY_BATCH_SIZE,
  chapterId,
  inferScalePlan,
  volumeId,
} from "../lib/planningScale";
import { Badge, Button, Card, Input, Label } from "../components/primitives";
import "./PlanningPage.css";

export function PlanningPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [targetWords, setTargetWords] = useState(3_000_000);
  const [avgChapterWords, setAvgChapterWords] = useState(3000);
  const [chapterPage, setChapterPage] = useState(0);
  const [activeVolumeId, setActiveVolumeId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, ChapterBlueprintRecommendation>>(
    {},
  );
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
  const CHAPTERS_PER_PAGE = 24;

  const statusQuery = useQuery({
    queryKey: ["project-status", projectId],
    queryFn: () => api.getProjectStatus(projectId!),
    enabled: !!projectId,
  });

  const outlinesQuery = useQuery({
    queryKey: ["outlines", projectId],
    queryFn: () => api.getOutlines(projectId!),
    enabled: !!projectId,
  });

  const generateMaster = useMutation({
    mutationFn: () => api.generateMasterOutline(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
    },
  });

  const generateThreads = useMutation({
    mutationFn: () =>
      api.generateNarrativeThreads(projectId!, {
        only_missing: true,
        apply: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
    },
  });

  const generateAllPending = useMutation({
    mutationFn: () =>
      api.generateOutlines(projectId!, {
        scope: "all",
        only_pending: true,
        apply: true,
        regenerate_master: false,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
      setDrafts({});
    },
  });

  const generateChapter = useMutation({
    mutationFn: (chapterId: string) =>
      api.generateChapterBlueprint(projectId!, chapterId),
    onSuccess: (data) => {
      setDrafts((prev) => ({ ...prev, [data.chapter_id]: data }));
    },
  });

  const applyBlueprint = useMutation({
    mutationFn: (params: {
      chapterId: string;
      title: string;
      beats: string[];
      constraints: string[];
      hard_constraints?: Record<string, unknown>;
      author_notes?: string;
      chapter_role?: string;
      primary_thread?: string;
      dormant_threads?: string[];
      status: string;
    }) =>
      api.putChapterBlueprint(projectId!, params.chapterId, {
        chapter_id: params.chapterId,
        title: params.title,
        beats: params.beats,
        constraints: params.constraints,
        hard_constraints: params.hard_constraints,
        author_notes: params.author_notes,
        chapter_role: params.chapter_role,
        primary_thread: params.primary_thread,
        dormant_threads: params.dormant_threads,
        status: params.status,
      }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
      setDrafts((prev) => {
        const next = { ...prev };
        delete next[variables.chapterId];
        return next;
      });
    },
  });

  const saveAuthorNotes = useMutation({
    mutationFn: (params: {
      chapterId: string;
      title: string;
      beats: string[];
      constraints: string[];
      hard_constraints?: Record<string, unknown>;
      author_notes: string;
      chapter_role?: string;
      primary_thread?: string;
      dormant_threads?: string[];
      status: string;
    }) =>
      api.putChapterBlueprint(projectId!, params.chapterId, {
        chapter_id: params.chapterId,
        title: params.title,
        beats: params.beats,
        constraints: params.constraints,
        hard_constraints: params.hard_constraints,
        author_notes: params.author_notes,
        chapter_role: params.chapter_role,
        primary_thread: params.primary_thread,
        dormant_threads: params.dormant_threads,
        status: params.status,
      }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
      setNoteDrafts((prev) => {
        const next = { ...prev };
        delete next[variables.chapterId];
        return next;
      });
    },
  });

  const applyScalePlan = useMutation({
    mutationFn: async (params: {
      totalChapters: number;
      volumeCount: number;
      chaptersPerVolume: number;
      theme: string;
    }) => {
      const volumePromises: Array<Promise<unknown>> = [];
      for (let i = 0; i < params.volumeCount; i += 1) {
        const start = i * params.chaptersPerVolume + 1;
        const end = Math.min(params.totalChapters, (i + 1) * params.chaptersPerVolume);
        volumePromises.push(
          api.putVolumeOutline(projectId!, volumeId(i), {
            title: `第${i + 1}卷`,
            arcs: [{ summary: `围绕主线阶段目标推进（第${start}-${end}章）` }],
            chapter_range: [start, end],
          }),
        );
      }

      const chapterRequests: Array<Promise<unknown>> = [];
      for (let i = 0; i < params.totalChapters; i += 1) {
        const chapterNo = i + 1;
        const id = chapterId(chapterNo);
        chapterRequests.push(
          api.putChapterBlueprint(projectId!, id, {
            chapter_id: id,
            title: `第${chapterNo}章`,
            beats: [],
            constraints: ["保持节奏与伏笔连续性"],
            status: "pending",
          }),
        );
      }

      await api.putMasterOutline(projectId!, {
        themes: [params.theme],
      });

      for (let i = 0; i < volumePromises.length; i += SCALE_APPLY_BATCH_SIZE) {
        await Promise.all(volumePromises.slice(i, i + SCALE_APPLY_BATCH_SIZE));
      }
      for (let i = 0; i < chapterRequests.length; i += SCALE_APPLY_BATCH_SIZE) {
        await Promise.all(chapterRequests.slice(i, i + SCALE_APPLY_BATCH_SIZE));
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
    },
  });

  const chapters = outlinesQuery.data?.chapters ?? [];
  const volumes = outlinesQuery.data?.volumes ?? [];
  const genre = statusQuery.data?.summary?.genre
    ? String(statusQuery.data.summary.genre)
    : "故事";
  const endingGoal = outlinesQuery.data?.master.ending_goal;

  const selectedVolume = useMemo(() => {
    if (!volumes.length) return null;
    if (activeVolumeId) {
      return volumes.find((volume) => volume.volume_id === activeVolumeId) ?? volumes[0];
    }
    return volumes[0];
  }, [activeVolumeId, volumes]);

  const volumesWithThreads = useMemo(
    () => volumes.filter((volume) => (volume.threads?.length ?? 0) > 0).length,
    [volumes],
  );

  const completion = outlinesQuery.data?.completion ?? 0;
  const recommendedCount = useMemo(
    () => chapters.filter((ch) => ch.beats.length === 0).length,
    [chapters],
  );

  const scale = useMemo(
    () => inferScalePlan(targetWords, avgChapterWords),
    [targetWords, avgChapterWords],
  );

  const pagedChapters = useMemo(() => {
    const start = chapterPage * CHAPTERS_PER_PAGE;
    return chapters.slice(start, start + CHAPTERS_PER_PAGE);
  }, [chapters, chapterPage]);

  const totalChapterPages = Math.max(
    1,
    Math.ceil(chapters.length / CHAPTERS_PER_PAGE),
  );

  const isGenerating =
    generateMaster.isPending ||
    generateThreads.isPending ||
    generateAllPending.isPending ||
    generateChapter.isPending;

  function displayBlueprint(chapter: ChapterBlueprint) {
    const draft = drafts[chapter.chapter_id];
    if (draft) return draft;
    if (chapter.beats.length > 0) {
      return {
        chapter_id: chapter.chapter_id,
        title: chapter.title,
        beats: chapter.beats,
        constraints: chapter.constraints,
        hard_constraints: chapter.hard_constraints,
        author_notes: chapter.author_notes,
        chapter_role: chapter.chapter_role,
        primary_thread: chapter.primary_thread,
        dormant_threads: chapter.dormant_threads,
        status: chapter.status,
      };
    }
    return null;
  }

  function hardConstraintSummary(hard?: Record<string, unknown>) {
    if (!hard || Object.keys(hard).length === 0) return null;
    const primary = String(hard.primary_thread ?? "");
    const role = String(hard.chapter_role ?? "");
    const dormant = Array.isArray(hard.dormant_threads)
      ? (hard.dormant_threads as string[]).join("、")
      : "";
    const goal = String(hard.narrative_goal ?? "");
    const parts = [
      role && `角色 ${role}`,
      primary && `主推 ${primary}`,
      dormant && `休眠 ${dormant}`,
      goal && `目标 ${goal}`,
    ].filter(Boolean);
    return parts.length ? parts.join(" · ") : null;
  }

  function priorityLabel(curve: string) {
    if (curve === "high_early") return "卷初主推";
    if (curve === "low_early_high_mid") return "卷初休眠";
    if (curve === "steady") return "稳步推进";
    return curve;
  }

  function priorityVariant(curve: string): "accent" | "warning" | "default" {
    if (curve === "high_early") return "accent";
    if (curve === "low_early_high_mid") return "warning";
    return "default";
  }

  if (!projectId) return null;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">规划</h1>
      <p className="page-subtitle">
        基于 Story Bible 与总纲，用 DeepSeek 生成可执行章节蓝图
      </p>

      <div className="planning-page__stats">
        <Card padding="md">
          <div className="planning-page__stat-value">{chapters.length}</div>
          <div className="planning-page__stat-label">章节蓝图</div>
        </Card>
        <Card padding="md">
          <div className="planning-page__stat-value">
            {outlinesQuery.data?.volumes.length ?? 0}
          </div>
          <div className="planning-page__stat-label">分卷数</div>
        </Card>
        <Card padding="md">
          <div className="planning-page__stat-value">{completion.toFixed(1)}%</div>
          <div className="planning-page__stat-label">规划完成度</div>
        </Card>
        <Card padding="md">
          <div className="planning-page__stat-value">{recommendedCount}</div>
          <div className="planning-page__stat-label">待生成章节</div>
        </Card>
      </div>

      <Card padding="md" className="planning-page__ai">
        <h3 style={{ marginBottom: "var(--space-3)" }}>AI 蓝图生成</h3>
        {endingGoal && (
          <p className="planning-page__ending-goal">
            全书终局目标：{endingGoal}
          </p>
        )}
        <div className="row" style={{ flexWrap: "wrap", gap: "var(--space-3)" }}>
          <Button
            variant="secondary"
            disabled={isGenerating || chapters.length === 0}
            onClick={() => generateMaster.mutate()}
          >
            <Sparkles size={14} strokeWidth={1.5} />
            {generateMaster.isPending ? "生成总纲中…" : "从设定集生成总纲"}
          </Button>
          <Button
            variant="secondary"
            disabled={
              isGenerating || (outlinesQuery.data?.volumes.length ?? 0) === 0
            }
            onClick={() => generateThreads.mutate()}
          >
            <Sparkles size={14} strokeWidth={1.5} />
            {generateThreads.isPending
              ? "生成叙事线程中…"
              : "AI 自动生成叙事线程"}
          </Button>
          <Button
            variant="primary"
            disabled={isGenerating || chapters.length === 0}
            onClick={() => generateAllPending.mutate()}
          >
            <Sparkles size={14} strokeWidth={1.5} />
            {generateAllPending.isPending
              ? "批量生成中…"
              : "批量生成待填章节蓝图"}
          </Button>
        </div>
        <p className="planning-page__hint">
          叙事线程无需手填：生成总纲时会一并产出；也可单独点「AI
          自动生成叙事线程」补全旧项目。生成蓝图前若缺线程会自动补齐。
        </p>
        {chapters.length > 50 && (
          <p className="planning-page__hint">
            章节较多时批量生成可能需要数分钟，请保持页面开启。
          </p>
        )}
        {(generateMaster.isError ||
          generateThreads.isError ||
          generateAllPending.isError) && (
          <div className="planning-page__hint">
            <Badge variant="danger">
              {
                (
                  (generateMaster.error ||
                    generateThreads.error ||
                    generateAllPending.error) as Error
                ).message
              }
            </Badge>
          </div>
        )}
        {generateThreads.isSuccess && (
          <div className="planning-page__hint">
            <Badge variant="success">
              已为 {generateThreads.data?.applied ?? 0} 卷写入叙事线程
              {generateThreads.data?.skipped
                ? `（跳过已有 ${generateThreads.data.skipped} 卷）`
                : ""}
            </Badge>
          </div>
        )}
        {generateAllPending.isSuccess && (
          <div className="planning-page__hint">
            <Badge variant="success">
              已应用 {generateAllPending.data?.applied ?? 0} 章蓝图
            </Badge>
          </div>
        )}
      </Card>

      <Card padding="md" className="planning-page__threads">
        <div className="planning-page__threads-header">
          <h3>分卷叙事线程</h3>
          <Badge variant={volumesWithThreads > 0 ? "success" : "warning"}>
            {volumesWithThreads}/{volumes.length} 卷已配置
          </Badge>
        </div>
        <p className="planning-page__hint" style={{ marginTop: 0 }}>
          只读预览：由 AI 生成总纲或「自动生成叙事线程」写入，写作与蓝图调度会按这些线程执行。
        </p>

        {volumes.length === 0 ? (
          <p className="planning-page__empty-beat">
            暂无分卷。请先做长篇规模推导，再生成总纲或叙事线程。
          </p>
        ) : (
          <div className="planning-page__threads-layout">
            <div className="planning-page__volume-list">
              {volumes.map((volume: VolumeOutline) => {
                const threadCount = volume.threads?.length ?? 0;
                const active =
                  (selectedVolume?.volume_id ?? "") === volume.volume_id;
                return (
                  <button
                    key={volume.volume_id}
                    type="button"
                    className={`planning-page__volume-item${
                      active ? " planning-page__volume-item--active" : ""
                    }`}
                    onClick={() => setActiveVolumeId(volume.volume_id)}
                  >
                    <div className="planning-page__volume-item-title">
                      {volume.title || volume.volume_id}
                    </div>
                    <div className="planning-page__volume-item-meta">
                      {volume.volume_id}
                      {volume.chapter_range?.length >= 2
                        ? ` · 第${volume.chapter_range[0]}-${volume.chapter_range[1]}章`
                        : ""}
                      {" · "}
                      {threadCount > 0 ? `${threadCount} 条线程` : "未配置"}
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="planning-page__thread-detail">
              {selectedVolume ? (
                <>
                  <div className="planning-page__thread-detail-head">
                    <h4>
                      {selectedVolume.title || selectedVolume.volume_id}
                    </h4>
                    <div className="row" style={{ gap: "var(--space-2)" }}>
                      <Badge>{selectedVolume.volume_id}</Badge>
                      {selectedVolume.chapter_range?.length >= 2 && (
                        <Badge>
                          第{selectedVolume.chapter_range[0]}-
                          {selectedVolume.chapter_range[1]}章
                        </Badge>
                      )}
                    </div>
                  </div>

                  {selectedVolume.opening_focus && (
                    <div className="planning-page__thread-focus">
                      <div className="planning-page__thread-focus-label">
                        卷初焦点
                      </div>
                      <p>{selectedVolume.opening_focus}</p>
                    </div>
                  )}
                  {selectedVolume.stage_goal && (
                    <div className="planning-page__thread-focus">
                      <div className="planning-page__thread-focus-label">
                        卷阶段目标（中后段）
                      </div>
                      <p>{selectedVolume.stage_goal}</p>
                    </div>
                  )}

                  {(selectedVolume.threads?.length ?? 0) === 0 ? (
                    <p className="planning-page__empty-beat">
                      本卷尚无叙事线程，请点击上方「AI 自动生成叙事线程」。
                    </p>
                  ) : (
                    <div className="planning-page__thread-cards">
                      {selectedVolume.threads!.map((thread: NarrativeThread) => (
                        <div
                          key={thread.id}
                          className="planning-page__thread-card"
                        >
                          <div className="planning-page__thread-card-head">
                            <strong>
                              {thread.label || thread.id}
                            </strong>
                            <div className="row" style={{ gap: "var(--space-2)" }}>
                              <Badge>{thread.id}</Badge>
                              <Badge
                                variant={priorityVariant(thread.priority_curve)}
                              >
                                {priorityLabel(thread.priority_curve)}
                              </Badge>
                            </div>
                          </div>

                          {(thread.stages?.length ?? 0) > 0 && (
                            <div className="planning-page__thread-section">
                              <div className="planning-page__thread-section-title">
                                推进台阶
                              </div>
                              <ol className="planning-page__thread-stages">
                                {thread.stages!.map((stage) => (
                                  <li key={stage.id}>
                                    <span className="planning-page__stage-label">
                                      L{stage.level} {stage.label || stage.id}
                                    </span>
                                    {stage.ceiling && (
                                      <span className="planning-page__stage-ceiling">
                                        {stage.ceiling}
                                      </span>
                                    )}
                                  </li>
                                ))}
                              </ol>
                            </div>
                          )}

                          {(thread.milestones?.length ?? 0) > 0 && (
                            <div className="planning-page__thread-section">
                              <div className="planning-page__thread-section-title">
                                里程碑
                              </div>
                              <ul className="planning-page__thread-milestones">
                                {thread.milestones!.map((milestone) => (
                                  <li key={milestone.id}>
                                    <Badge variant="default">
                                      ch_{String(milestone.earliest_chapter).padStart(3, "0")}
                                    </Badge>
                                    <span>{milestone.summary}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="planning-page__empty-beat">请选择左侧分卷</p>
              )}
            </div>
          </div>
        )}
      </Card>

      <Card padding="md" className="planning-page__scale">
        <h3 style={{ marginBottom: "var(--space-4)" }}>长篇规模推导</h3>
        <div className="planning-page__scale-grid">
          <div>
            <Label htmlFor="targetWords">目标总字数</Label>
            <Input
              id="targetWords"
              type="number"
              min={10000}
              max={10000000}
              step={10000}
              value={targetWords}
              onChange={(e) => setTargetWords(Number(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="avgChapterWords">章均字数</Label>
            <Input
              id="avgChapterWords"
              type="number"
              min={1000}
              step={100}
              value={avgChapterWords}
              onChange={(e) => setAvgChapterWords(Number(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="inferredChapters">推导章节数</Label>
            <Input id="inferredChapters" value={String(scale.totalChapters)} readOnly />
          </div>
        </div>
        <div className="planning-page__scale-result">
          <Badge variant="accent">建议分卷数：{scale.volumeCount}</Badge>
          <Badge>每卷约 {scale.chaptersPerVolume} 章</Badge>
          <Badge>预计总章数：{scale.totalChapters}</Badge>
          {scale.showPerformanceWarning && !scale.exceedsHardLimit && (
            <Badge variant="warning">
              章节较多，应用时可能需要数十秒；规划列表已分页展示
            </Badge>
          )}
          {scale.exceedsHardLimit && (
            <Badge variant="danger">
              章节数超过上限（{scale.totalChapters} &gt; 2000），请提高章均字数或降低目标总字数
            </Badge>
          )}
        </div>
        <Button
          variant="primary"
          disabled={applyScalePlan.isPending || scale.exceedsHardLimit}
          onClick={() =>
            applyScalePlan.mutate({
              totalChapters: scale.totalChapters,
              volumeCount: scale.volumeCount,
              chaptersPerVolume: scale.chaptersPerVolume,
              theme: genre,
            })
          }
        >
          <Sparkles size={14} strokeWidth={1.5} />
          {applyScalePlan.isPending ? "正在应用蓝图…" : "应用规模推导到大纲"}
        </Button>
        <p className="planning-page__hint">
          建议顺序：先应用规模推导 → 生成总纲 → 批量生成章节蓝图
        </p>
      </Card>

      {outlinesQuery.isLoading && <p className="animate-pulse-subtle">加载规划数据…</p>}

      {chapters.length === 0 && !outlinesQuery.isLoading && (
        <Card padding="md">
          <p>暂无章节蓝图，请先完成规模推导或从写作流程创建章节。</p>
        </Card>
      )}

      <div className="planning-page__grid">
        {chapters.length > CHAPTERS_PER_PAGE && (
          <div className="planning-page__pagination">
            <Button
              variant="ghost"
              size="sm"
              disabled={chapterPage === 0}
              onClick={() => setChapterPage((p) => Math.max(0, p - 1))}
            >
              上一页
            </Button>
            <span>
              第 {chapterPage + 1}/{totalChapterPages} 页（共 {chapters.length} 章）
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={chapterPage >= totalChapterPages - 1}
              onClick={() =>
                setChapterPage((p) => Math.min(totalChapterPages - 1, p + 1))
              }
            >
              下一页
            </Button>
          </div>
        )}
        {pagedChapters.map((chapter) => {
          const blueprint = displayBlueprint(chapter);
          const dirty = !blueprint || chapter.beats.length === 0;
          const title = blueprint?.title || chapter.title || chapter.chapter_id;
          const beats = blueprint?.beats ?? [];
          const softConstraints = blueprint?.constraints ?? [];
          const hardSummary = hardConstraintSummary(
            blueprint?.hard_constraints ?? chapter.hard_constraints,
          );
          const savedNotes =
            blueprint?.author_notes ?? chapter.author_notes ?? "";
          const notesValue =
            noteDrafts[chapter.chapter_id] !== undefined
              ? noteDrafts[chapter.chapter_id]
              : savedNotes;
          const notesDirty = notesValue !== savedNotes;

          return (
            <Card key={chapter.chapter_id} padding="md">
              <div className="planning-page__chapter-title">{title}</div>
              <div className="planning-page__chapter-meta">
                {chapter.chapter_id} · 当前状态 {chapter.status}
                {(blueprint?.primary_thread || chapter.primary_thread) && (
                  <>
                    {" "}
                    · 主推 {blueprint?.primary_thread || chapter.primary_thread}
                  </>
                )}
              </div>

              <div className="planning-page__recommendation">
                <Badge variant={dirty ? "warning" : "success"}>
                  {dirty ? "待生成蓝图" : "已具备蓝图"}
                </Badge>
                {drafts[chapter.chapter_id] && (
                  <Badge variant="accent">预览中</Badge>
                )}
              </div>

              <div className="planning-page__beats">
                {beats.length > 0 ? (
                  beats.map((beat, i) => (
                    <div key={i} className="planning-page__beat">
                      - {beat}
                    </div>
                  ))
                ) : (
                  <p className="planning-page__empty-beat">点击生成 AI 蓝图</p>
                )}
              </div>

              {hardSummary && (
                <p className="planning-page__hard-constraints">
                  硬约束：{hardSummary}
                </p>
              )}

              <div className="planning-page__author-notes">
                <Label htmlFor={`notes-${chapter.chapter_id}`}>本章备注</Label>
                <textarea
                  id={`notes-${chapter.chapter_id}`}
                  className="planning-page__author-notes-input"
                  rows={2}
                  value={notesValue}
                  placeholder="例如：本章多写教室氛围，不要强行推进感情线"
                  onChange={(e) =>
                    setNoteDrafts((prev) => ({
                      ...prev,
                      [chapter.chapter_id]: e.target.value,
                    }))
                  }
                />
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={!notesDirty || saveAuthorNotes.isPending}
                  onClick={() =>
                    saveAuthorNotes.mutate({
                      chapterId: chapter.chapter_id,
                      title: title,
                      beats: beats.length ? beats : chapter.beats,
                      constraints: softConstraints,
                      hard_constraints:
                        blueprint?.hard_constraints ?? chapter.hard_constraints,
                      author_notes: notesValue,
                      chapter_role:
                        blueprint?.chapter_role ?? chapter.chapter_role,
                      primary_thread:
                        blueprint?.primary_thread ?? chapter.primary_thread,
                      dormant_threads:
                        blueprint?.dormant_threads ?? chapter.dormant_threads,
                      status: chapter.status || "pending",
                    })
                  }
                >
                  保存备注
                </Button>
              </div>

              <div className="planning-page__card-actions">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={generateChapter.isPending}
                  onClick={() => generateChapter.mutate(chapter.chapter_id)}
                >
                  <Sparkles size={14} strokeWidth={1.5} />
                  生成 AI 蓝图
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  disabled={!blueprint || applyBlueprint.isPending}
                  onClick={() =>
                    blueprint &&
                    applyBlueprint.mutate({
                      chapterId: chapter.chapter_id,
                      title: blueprint.title,
                      beats: blueprint.beats,
                      constraints: blueprint.constraints,
                      hard_constraints: blueprint.hard_constraints,
                      author_notes: notesValue || blueprint.author_notes || "",
                      chapter_role: blueprint.chapter_role,
                      primary_thread: blueprint.primary_thread,
                      dormant_threads: blueprint.dormant_threads,
                      status: "ready",
                    })
                  }
                >
                  应用蓝图
                </Button>
              </div>
              {softConstraints.length > 0 && (
                <p className="planning-page__constraints">
                  软约束：{softConstraints.join("；")}
                </p>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
