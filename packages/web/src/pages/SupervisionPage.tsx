import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import type { PendingItem } from "../api/types";
import { api } from "../api/client";
import { ApprovalModal, Toast } from "../components/feedback";
import { Badge, Button, Card } from "../components/primitives";
import "./SupervisionPage.css";

type ResolveAction = "apply" | "ignore" | "rollback";

const ACTION_META: Record<
  ResolveAction,
  { title: string; confirm: string; variant: "primary" | "danger" }
> = {
  apply: { title: "确认变更", confirm: "确认应用", variant: "primary" },
  ignore: { title: "忽略风险", confirm: "确认忽略", variant: "primary" },
  rollback: { title: "回滚改动", confirm: "确认回滚", variant: "danger" },
};

const RISK_VARIANT = {
  low: "success",
  medium: "warning",
  high: "danger",
} as const;

function riskLabel(level: PendingItem["risk_level"]) {
  return { low: "低", medium: "中", high: "高" }[level];
}

export function SupervisionPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [pendingAction, setPendingAction] = useState<{
    item: PendingItem;
    action: ResolveAction;
  } | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const supervisionQuery = useQuery({
    queryKey: ["supervision", projectId],
    queryFn: () => api.getSupervision(projectId!),
    enabled: !!projectId,
  });

  const resolve = useMutation({
    mutationFn: (params: { pendingId: string; action: ResolveAction }) =>
      api.resolveSupervision(projectId!, {
        pending_id: params.pendingId,
        action: params.action,
        actor: "user",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supervision", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-status", projectId] });
      setToast({ message: "已处理监督事项", type: "success" });
      setPendingAction(null);
    },
    onError: (err: Error) => {
      setToast({ message: err.message || "处理失败", type: "error" });
    },
  });

  const distill = useMutation({
    mutationFn: () => api.runDistill(projectId!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["supervision", projectId] });
      setToast({
        message: `已提炼 ${data.added_rules.length} 条风格规则`,
        type: "success",
      });
    },
    onError: (err: Error) => setToast({ message: err.message || "提炼失败", type: "error" }),
  });

  const dream = useMutation({
    mutationFn: () => api.runDream(projectId!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["supervision", projectId] });
      setToast({
        message: data.notes_updated ? "项目记忆已整理" : "记忆无需整理",
        type: "success",
      });
    },
    onError: (err: Error) => setToast({ message: err.message || "整理失败", type: "error" }),
  });

  const batchResolve = useMutation({
    mutationFn: async (action: ResolveAction) => {
      if (!data) return;
      const candidates =
        action === "rollback"
          ? data.pending_items.filter((x) => x.risk_level === "high")
          : data.pending_items;
      await Promise.all(
        candidates.map((item) =>
          api.resolveSupervision(projectId!, {
            pending_id: item.id,
            action,
            actor: "user",
          }),
        ),
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supervision", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project-status", projectId] });
      setToast({ message: "批量操作已完成", type: "success" });
    },
    onError: (err: Error) => {
      setToast({ message: err.message || "批量处理失败", type: "error" });
    },
  });

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const data = supervisionQuery.data;
  const highRiskCount =
    data?.pending_items.filter((item) => item.risk_level === "high").length ?? 0;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">监督</h1>
      <p className="page-subtitle">查看风险项并执行确认、忽略或回滚</p>

      <Card padding="md" className="supervision-page__health">
        <div className="row">
          <Badge variant="accent">整体 {data?.health.overall ?? "-"}</Badge>
          <Badge>会话 {data?.health.session ?? "-"}</Badge>
          <Badge variant={(data?.health.pending_count ?? 0) > 0 ? "warning" : "success"}>
            待处理 {data?.health.pending_count ?? 0}
          </Badge>
          <Button
            size="sm"
            variant="ghost"
            disabled={dream.isPending}
            onClick={() => dream.mutate()}
          >
            整理记忆
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={distill.isPending}
            onClick={() => distill.mutate()}
          >
            提炼规则
          </Button>
        </div>
      </Card>

      {supervisionQuery.isLoading && <p className="animate-pulse-subtle">加载监督数据…</p>}

      {data && data.pending_items.length > 0 && (
        <Card padding="md" className="supervision-page__batch">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="row">
              <Badge variant="warning">待处理 {data.pending_items.length}</Badge>
              <Badge variant="danger">高风险 {highRiskCount}</Badge>
            </div>
            <div className="row">
              <Button
                size="sm"
                variant="ghost"
                disabled={batchResolve.isPending}
                onClick={() => batchResolve.mutate("ignore")}
              >
                批量忽略
              </Button>
              <Button
                size="sm"
                variant="danger"
                disabled={batchResolve.isPending || highRiskCount === 0}
                onClick={() => batchResolve.mutate("rollback")}
              >
                一键回滚高风险
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="supervision-page__pending">
        {data?.pending_items.map((item) => (
          <Card key={item.id} padding="md">
            <div className="row">
              <span className="supervision-page__item-title">{item.item_type}</span>
              <Badge variant={RISK_VARIANT[item.risk_level]}>
                {riskLabel(item.risk_level)}
              </Badge>
            </div>
            <p className="supervision-page__item-summary">{item.summary}</p>
            {item.risk_level === "high" ? (
              <div className="supervision-page__actions">
                <Button size="sm" onClick={() => setPendingAction({ item, action: "apply" })}>
                  确认
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setPendingAction({ item, action: "ignore" })}
                >
                  忽略
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => setPendingAction({ item, action: "rollback" })}
                >
                  回滚
                </Button>
              </div>
            ) : (
              <Badge variant="success">低中风险自动处理或无需确认</Badge>
            )}
          </Card>
        ))}
      </div>

      <Card padding="md" className="supervision-page__logs">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: "var(--space-3)" }}>
          <h3>最近动作</h3>
          <Link to={`/projects/${projectId}/llm-logs`}>查看 LLM 调用日志</Link>
        </div>
        {data?.recent_actions.slice(0, 12).map((action, index) => (
          <div key={index} className="supervision-page__log-line">
            {new Date(action.timestamp).toLocaleString("zh-CN")} · {action.action_type}
            {action.diff_summary ? ` — ${action.diff_summary}` : ""}
          </div>
        ))}
      </Card>

      <ApprovalModal
        open={!!pendingAction}
        title={
          pendingAction
            ? `${ACTION_META[pendingAction.action].title}（${pendingAction.item.item_type}）`
            : ""
        }
        description={pendingAction?.item.summary ?? ""}
        confirmLabel={pendingAction ? ACTION_META[pendingAction.action].confirm : "确认"}
        confirmVariant={pendingAction ? ACTION_META[pendingAction.action].variant : "primary"}
        loading={resolve.isPending}
        onCancel={() => setPendingAction(null)}
        onConfirm={() => {
          if (!pendingAction) return;
          resolve.mutate({
            pendingId: pendingAction.item.id,
            action: pendingAction.action,
          });
        }}
      />
      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
}
