import { useState, useEffect, useRef } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, Play, RotateCcw } from "lucide-react";
import { api, subscribeJobEvents } from "../api/client";
import { ChapterReader, JobProgressPanel } from "../components/features";
import { Badge, Button, Card, Input, Label, Textarea } from "../components/primitives";
import {
  DEFAULT_REWRITE_INSTRUCTION,
  DEFAULT_WRITE_INSTRUCTION,
} from "../constants/prompts";
import "./WritePage.css";

export function WritePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [instruction, setInstruction] = useState(DEFAULT_WRITE_INSTRUCTION);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [events, setEvents] = useState<string[]>([]);
  const [explicitChapterId, setExplicitChapterId] = useState<string | null>(null);
  const [displayChapterId, setDisplayChapterId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [maxMode, setMaxMode] = useState(false);
  const [volumeLimit, setVolumeLimit] = useState(3);
  const unsubRef = useRef<(() => void) | null>(null);

  const { data: status } = useQuery({
    queryKey: ["project-status", projectId],
    queryFn: () => api.getProjectStatus(projectId!),
    enabled: !!projectId,
  });

  const { data: chapter, refetch: refetchChapter } = useQuery({
    queryKey: ["chapter", projectId, displayChapterId],
    queryFn: () => api.getChapter(projectId!, displayChapterId!),
    enabled: !!projectId && !!displayChapterId,
  });

  useEffect(() => {
    const fromUrl = searchParams.get("chapter_id");
    if (!fromUrl) return;
    setExplicitChapterId(fromUrl);
    setDisplayChapterId(fromUrl);
    setInstruction(DEFAULT_REWRITE_INSTRUCTION);
  }, [searchParams]);

  const write = useMutation({
    mutationFn: () =>
      api.writeChapter(projectId!, {
        instruction,
        chapter_id: explicitChapterId ?? undefined,
        max_mode: maxMode || undefined,
      }),
    onSuccess: (res) => {
      setJobId(res.job_id);
      setEvents([]);
      setProgress(5);
      setError("");
      setNotice("");
    },
    onError: (err: Error) => setError(err.message),
  });

  const writeVolume = useMutation({
    mutationFn: () =>
      api.writeVolume(projectId!, {
        instruction,
        limit: volumeLimit,
        max_mode: maxMode || null,
      }),
    onSuccess: (res) => {
      setJobId(res.job_id);
      setEvents([]);
      setProgress(5);
      setError("");
      setNotice("");
    },
    onError: (err: Error) => setError(err.message),
  });

  useEffect(() => {
    if (!projectId || !jobId) return;

    unsubRef.current?.();
    unsubRef.current = subscribeJobEvents(
      projectId,
      jobId,
      (evt) => {
        setEvents((prev) => [...prev.slice(-19), `[${evt.type}] ${JSON.stringify(evt.data)}`]);

        if (evt.type === "job.progress") {
          const pct = evt.data.percent as number | undefined;
          if (typeof pct === "number") setProgress(pct);
        }
        if (evt.type === "job.chunk") {
          setProgress((p) => Math.min(95, p + 2));
        }
        if (evt.type === "job.complete") {
          setProgress(100);
          const resultChapterId = evt.data.chapter_id as string | undefined;
          if (resultChapterId) {
            setDisplayChapterId(resultChapterId);
            refetchChapter();
          }
          if (evt.data.kind === "volume") {
            const done = (evt.data.chapters_completed as string[]) || [];
            const last = done[done.length - 1];
            if (last) {
              setDisplayChapterId(last);
              refetchChapter();
            }
            setNotice(
              `连写结束：完成 ${done.join("、") || "无"}（${evt.data.stopped_reason || ""}）`,
            );
          } else if (evt.data.goal_satisfied === false) {
            const summary = (evt.data.goal_summary as string) || "独立验收未通过";
            setNotice(`本章未标为完成：${summary}`);
          }
        }
        if (evt.type === "job.error") {
          setError((evt.data.message as string) || "写作任务失败");
        }
      },
      () => {
        /* SSE may close on completion */
      },
    );

    return () => unsubRef.current?.();
  }, [projectId, jobId, refetchChapter]);

  useEffect(() => {
    if (!projectId || !jobId) return;

    const poll = setInterval(async () => {
      try {
        const job = await api.getJob(projectId, jobId);
        if (job.status === "completed" && job.result) {
          const result = job.result;
          if (result.kind === "volume") {
            const last = result.chapters_completed.at(-1);
            if (last) setDisplayChapterId(last);
            setNotice(
              `连写结束：完成 ${result.chapters_completed.join("、") || "无"}（${result.stopped_reason}）`,
            );
          } else if ("chapter_id" in result && result.chapter_id) {
            setDisplayChapterId(result.chapter_id);
            if (result.goal_satisfied === false) {
              setNotice(`本章未标为完成：${result.goal_summary || "独立验收未通过"}`);
            }
          }
          setProgress(100);
          refetchChapter();
          clearInterval(poll);
        }
        if (job.status === "failed") {
          setError(job.error || "写作任务失败");
          clearInterval(poll);
        }
      } catch {
        /* ignore poll errors */
      }
    }, 2000);

    return () => clearInterval(poll);
  }, [projectId, jobId, refetchChapter]);

  const nextChapterNum = (status?.chapter_count ?? 0) + 1;
  const suggestedChapterId = `ch_${String(nextChapterNum).padStart(3, "0")}`;
  const isRewriteMode = !!explicitChapterId;

  const switchToNextChapter = () => {
    setExplicitChapterId(null);
    setInstruction(DEFAULT_WRITE_INSTRUCTION);
    setSearchParams({});
  };

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">写作</h1>
      <p className="page-subtitle">
        触发 AI 写作任务，实时查看进度与生成内容
      </p>

      <Card padding="md" className="write-page__form">
        <div>
          <Label htmlFor="instruction">写作指令</Label>
          <Textarea
            id="instruction"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            rows={3}
          />
        </div>
        <div className="row">
          {isRewriteMode ? (
            <Badge variant="warning">重写目标: {explicitChapterId}</Badge>
          ) : (
            <Badge>建议章节 ID: {suggestedChapterId}</Badge>
          )}
          {jobId && <Badge variant="accent">Job: {jobId.slice(0, 8)}</Badge>}
        </div>
        {error && <p className="write-page__error">{error}</p>}
        {notice && <p className="write-page__notice">{notice}</p>}
        <div className="row">
          <label className="row" style={{ gap: "var(--space-2)" }}>
            <input
              type="checkbox"
              checked={maxMode}
              onChange={(e) => setMaxMode(e.target.checked)}
            />
            <span>并行选优（Max Mode）</span>
          </label>
          <div className="row" style={{ gap: "var(--space-2)" }}>
            <Label htmlFor="volume-limit">连写章数</Label>
            <Input
              id="volume-limit"
              type="number"
              min={1}
              max={8}
              value={volumeLimit}
              onChange={(e) =>
                setVolumeLimit(Math.max(1, Math.min(8, Number(e.target.value) || 3)))
              }
            />
          </div>
        </div>
        <div className="row">
          <Button
            onClick={() => write.mutate()}
            disabled={
              write.isPending ||
              writeVolume.isPending ||
              (!!jobId && progress > 0 && progress < 100)
            }
          >
            {write.isPending ? (
              <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
            ) : isRewriteMode ? (
              <RotateCcw size={16} strokeWidth={1.5} />
            ) : (
              <Play size={16} strokeWidth={1.5} />
            )}
            {isRewriteMode ? "重写本章" : "开始写作"}
          </Button>
          <Button
            variant="ghost"
            onClick={() => writeVolume.mutate()}
            disabled={
              isRewriteMode ||
              write.isPending ||
              writeVolume.isPending ||
              (!!jobId && progress > 0 && progress < 100)
            }
          >
            {writeVolume.isPending ? (
              <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
            ) : (
              <Play size={16} strokeWidth={1.5} />
            )}
            连写 {volumeLimit} 章
          </Button>
          {isRewriteMode && (
            <Button variant="ghost" onClick={switchToNextChapter}>
              切换为写下一章
            </Button>
          )}
        </div>
      </Card>

      {(jobId || progress > 0) && (
        <JobProgressPanel progress={progress} events={events} />
      )}

      {chapter && <ChapterReader chapter={chapter} />}
    </div>
  );
}
