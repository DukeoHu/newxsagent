import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { api } from "../api/client";
import type { ExploreRecord } from "../api/types";
import { Badge, Button, Card, Input, Label, Textarea } from "../components/primitives";
import { Toast } from "../components/feedback";
import { DEFAULT_EXPLORE_PROMPT } from "../constants/prompts";
import "./ExplorePage.css";

const RISK_VARIANT = {
  low: "success",
  medium: "warning",
  high: "danger",
} as const;

export function ExplorePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [chapterId, setChapterId] = useState("ch_001");
  const [prompt, setPrompt] = useState(DEFAULT_EXPLORE_PROMPT);
  const [count, setCount] = useState(3);
  const [record, setRecord] = useState<ExploreRecord | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(
    null,
  );

  const outlinesQuery = useQuery({
    queryKey: ["outlines", projectId],
    queryFn: () => api.getOutlines(projectId!),
    enabled: !!projectId,
  });

  const createExplore = useMutation({
    mutationFn: () =>
      api.createExplore(projectId!, {
        chapter_id: chapterId || undefined,
        prompt,
        count,
      }),
    onSuccess: (data) => {
      setRecord(data);
      setToast({ type: "success", message: "探索方案已生成" });
    },
    onError: (err: Error) => setToast({ type: "error", message: err.message }),
  });

  const adoptOption = useMutation({
    mutationFn: (optionId: string) =>
      api.adoptExplore(projectId!, record!.explore_id, { option_id: optionId, actor: "user" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outlines", projectId] });
      setToast({ type: "success", message: "方案已采纳到章节蓝图" });
    },
    onError: (err: Error) => setToast({ type: "error", message: err.message }),
  });

  const chapterChoices =
    outlinesQuery.data?.chapters.map((x) => x.chapter_id) ?? ["ch_001", "ch_002", "ch_003"];

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">探索采纳</h1>
      <p className="page-subtitle">生成多方案并由评审标出更稳妥的一项，再采纳到章节蓝图</p>

      <Card padding="md" style={{ marginBottom: "var(--space-6)" }}>
        <div className="explore-page__controls">
          <div>
            <Label htmlFor="explore-chapter">目标章节</Label>
            <select
              id="explore-chapter"
              className="input"
              value={chapterId}
              onChange={(e) => setChapterId(e.target.value)}
            >
              {chapterChoices.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label htmlFor="explore-count">方案数量</Label>
            <Input
              id="explore-count"
              type="number"
              min={1}
              max={5}
              value={count}
              onChange={(e) => setCount(Math.max(1, Math.min(5, Number(e.target.value) || 3)))}
            />
          </div>

          <div className="explore-page__controls-full">
            <Label htmlFor="explore-prompt">探索指令</Label>
            <Textarea
              id="explore-prompt"
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
        </div>

        <Button
          onClick={() => createExplore.mutate()}
          disabled={createExplore.isPending || !prompt.trim()}
        >
          <Sparkles size={16} strokeWidth={1.5} />
          生成探索方案
        </Button>
      </Card>

      {record && (
        <div className="explore-page__options">
          {record.judge_reason && (
            <p className="explore-page__summary">评审：{record.judge_reason}</p>
          )}
          {record.options.map((option) => (
            <Card key={option.option_id} padding="md">
              <div className="row">
                <h3 style={{ margin: 0 }}>{option.title}</h3>
                <Badge variant={RISK_VARIANT[option.risk_level]}>
                  {option.risk_level}
                </Badge>
                {record.recommended_option_id === option.option_id && (
                  <Badge variant="accent">评审推荐</Badge>
                )}
              </div>
              <p className="explore-page__summary">{option.summary}</p>
              <div className="explore-page__beats">
                {option.beats.map((beat, i) => (
                  <div key={i} className="explore-page__beat">
                    - {beat}
                  </div>
                ))}
              </div>
              <Button
                size="sm"
                onClick={() => adoptOption.mutate(option.option_id)}
                disabled={adoptOption.isPending}
              >
                采纳到 {option.chapter_id}
              </Button>
            </Card>
          ))}
        </div>
      )}

      {toast && <Toast type={toast.type} message={toast.message} />}
    </div>
  );
}
