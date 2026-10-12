import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useParams } from "react-router-dom";
import type { LLMLogEntry } from "../api/types";
import { api } from "../api/client";
import { Badge, Button, Card } from "../components/primitives";
import "./LLMLogsPage.css";

const TASK_LABELS: Record<string, string> = {
  prose: "正文写作",
  bible_sync: "设定同步",
  drift_detect: "漂移检测",
  fix: "修复建议",
  onboarding_question: "引导提问",
  onboarding_generate: "引导生成",
  outline_master: "大纲主线",
  outline_chapters: "章节蓝图",
  outline_threads: "叙事线程",
};

function taskLabel(task: string) {
  return TASK_LABELS[task] ?? task;
}

function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleString("zh-CN");
}

function PayloadBlock({
  label,
  value,
  truncated,
}: {
  label: string;
  value: string;
  truncated?: boolean;
}) {
  if (!value) return null;
  return (
    <div className="llm-logs-page__payload">
      <div className="llm-logs-page__payload-header">
        <span>{label}</span>
        {truncated && <Badge variant="warning">已截断</Badge>}
      </div>
      <pre className="llm-logs-page__payload-body">{value}</pre>
    </div>
  );
}

function LogEntryCard({
  entry,
  expanded,
  onToggle,
}: {
  entry: LLMLogEntry;
  expanded: boolean;
  onToggle: () => void;
}) {
  const statusVariant =
    entry.status === "ok" ? "success" : entry.status === "error" ? "danger" : "warning";

  return (
    <Card padding="md" className="llm-logs-page__entry">
      <button type="button" className="llm-logs-page__entry-header" onClick={onToggle}>
        <div className="llm-logs-page__entry-main">
          <div className="llm-logs-page__entry-title">
            <span>{taskLabel(entry.task)}</span>
            <Badge variant={statusVariant}>{entry.status}</Badge>
            {entry.json_mode && <Badge>JSON</Badge>}
          </div>
          <div className="llm-logs-page__entry-meta">
            {formatTime(entry.timestamp)} · {entry.llm_mode}/{entry.model} · {entry.latency_ms}ms
            {entry.job_id ? ` · job ${entry.job_id.slice(0, 8)}` : ""}
          </div>
          {!expanded && (
            <p className="llm-logs-page__entry-preview">
              {entry.prompt.slice(0, 160)}
              {entry.prompt.length > 160 ? "…" : ""}
            </p>
          )}
        </div>
        {expanded ? (
          <ChevronUp size={18} strokeWidth={1.5} />
        ) : (
          <ChevronDown size={18} strokeWidth={1.5} />
        )}
      </button>

      {expanded && (
        <div className="llm-logs-page__entry-detail">
          <div className="row llm-logs-page__entry-badges">
            <Badge>{entry.id.slice(0, 8)}</Badge>
            {entry.system_truncated && <Badge variant="warning">system 截断</Badge>}
            {entry.prompt_truncated && <Badge variant="warning">prompt 截断</Badge>}
            {entry.response_truncated && <Badge variant="warning">response 截断</Badge>}
          </div>
          <PayloadBlock label="System" value={entry.system} truncated={entry.system_truncated} />
          <PayloadBlock label="Prompt" value={entry.prompt} truncated={entry.prompt_truncated} />
          {entry.response && (
            <PayloadBlock
              label="Response"
              value={entry.response}
              truncated={entry.response_truncated}
            />
          )}
          {entry.error && (
            <PayloadBlock label="Error" value={entry.error} />
          )}
        </div>
      )}
    </Card>
  );
}

export function LLMLogsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [taskFilter, setTaskFilter] = useState<string>("all");

  const logsQuery = useQuery({
    queryKey: ["llm-logs", projectId],
    queryFn: () => api.listLLMLogs(projectId!),
    enabled: !!projectId,
    refetchInterval: 5000,
  });

  const entries = useMemo(() => {
    const list = [...(logsQuery.data ?? [])].reverse();
    if (taskFilter === "all") return list;
    return list.filter((entry) => entry.task === taskFilter);
  }, [logsQuery.data, taskFilter]);

  const taskOptions = useMemo(() => {
    const tasks = new Set((logsQuery.data ?? []).map((entry) => entry.task));
    return Array.from(tasks);
  }, [logsQuery.data]);

  return (
    <div className="animate-fade-in llm-logs-page">
      <h1 className="page-title">LLM 调用日志</h1>
      <p className="page-subtitle">查看每次发送给大模型的 system、prompt 与 response</p>

      <Card padding="md" className="llm-logs-page__toolbar">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row">
            <Badge variant="accent">共 {logsQuery.data?.length ?? 0} 条</Badge>
            <Badge>最近 50 条</Badge>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => logsQuery.refetch()}
            disabled={logsQuery.isFetching}
          >
            刷新
          </Button>
        </div>
        {taskOptions.length > 0 && (
          <div className="llm-logs-page__filters">
            <Button
              size="sm"
              variant={taskFilter === "all" ? "primary" : "ghost"}
              onClick={() => setTaskFilter("all")}
            >
              全部
            </Button>
            {taskOptions.map((task) => (
              <Button
                key={task}
                size="sm"
                variant={taskFilter === task ? "primary" : "ghost"}
                onClick={() => setTaskFilter(task)}
              >
                {taskLabel(task)}
              </Button>
            ))}
          </div>
        )}
      </Card>

      {logsQuery.isLoading && <p className="animate-pulse-subtle">加载 LLM 日志…</p>}

      {!logsQuery.isLoading && entries.length === 0 && (
        <Card padding="lg" className="llm-logs-page__empty">
          <p>暂无 LLM 调用记录。完成一次写作、引导或规划操作后，这里会显示发送给模型的完整内容。</p>
        </Card>
      )}

      <div className="llm-logs-page__list">
        {entries.map((entry) => (
          <LogEntryCard
            key={entry.id}
            entry={entry}
            expanded={expandedId === entry.id}
            onToggle={() =>
              setExpandedId((current) => (current === entry.id ? null : entry.id))
            }
          />
        ))}
      </div>
    </div>
  );
}
