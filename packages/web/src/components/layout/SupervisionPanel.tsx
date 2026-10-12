import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { api } from "../../api/client";
import type { PendingItem } from "../../api/types";
import { ApprovalModal, Toast } from "../feedback";
import { Badge, Button } from "../primitives";
import "./SupervisionPanel.css";

const RISK_VARIANT = {
  low: "success",
  medium: "warning",
  high: "danger",
} as const;

function riskLabel(level: PendingItem["risk_level"]) {
  return { low: "低", medium: "中", high: "高" }[level];
}

interface SupervisionPanelProps {
  projectId: string;
}

type ResolveAction = "apply" | "ignore" | "rollback";

const ACTION_META: Record<
  ResolveAction,
  { title: string; confirm: string; variant: "primary" | "danger" }
> = {
  apply: { title: "确认变更", confirm: "确认应用", variant: "primary" },
  ignore: { title: "忽略风险", confirm: "确认忽略", variant: "primary" },
  rollback: { title: "回滚改动", confirm: "确认回滚", variant: "danger" },
};

export function SupervisionPanel({ projectId }: SupervisionPanelProps) {
  const queryClient = useQueryClient();
  const [pendingAction, setPendingAction] = useState<{
    item: PendingItem;
    action: ResolveAction;
  } | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["supervision", projectId],
    queryFn: () => api.getSupervision(projectId),
    refetchInterval: 10_000,
  });

  const resolve = useMutation({
    mutationFn: (params: { pendingId: string; action: "apply" | "ignore" | "rollback" }) =>
      api.resolveSupervision(projectId, {
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

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const askForApproval = (item: PendingItem, action: ResolveAction) => {
    setPendingAction({ item, action });
  };

  const overall = data?.health.overall ?? 100;
  const healthVariant =
    overall >= 80 ? "success" : overall >= 50 ? "warning" : "danger";

  return (
    <aside className="supervision-panel" aria-label="监督面板">
      <div className="supervision-panel__header">
        <div className="supervision-panel__title">
          <Shield size={16} strokeWidth={1.5} />
          监督
        </div>
        {data && (
          <div className="supervision-panel__health">
            <span className="supervision-panel__score">{overall}</span>
            <Badge variant={healthVariant}>
              会话 {data.health.session}
            </Badge>
          </div>
        )}
      </div>

      <div className="supervision-panel__body">
        <div className="supervision-panel__section-title">待处理</div>

        {isLoading && (
          <p className="supervision-panel__empty animate-pulse-subtle">加载中…</p>
        )}

        {!isLoading && data?.pending_items.length === 0 && (
          <p className="supervision-panel__empty">暂无待处理事项</p>
        )}

        {data?.pending_items.map((item) => (
          <div key={item.id} className="supervision-panel__item">
            <div className="row" style={{ marginBottom: "var(--space-1)" }}>
              <span className="supervision-panel__item-title">{item.item_type}</span>
              <Badge variant={RISK_VARIANT[item.risk_level]}>
                {riskLabel(item.risk_level)}
              </Badge>
            </div>
            <p className="supervision-panel__item-desc">{item.summary}</p>
            {item.risk_level === "high" && (
              <div className="supervision-panel__item-actions">
                <Button
                  size="sm"
                  variant="primary"
                  disabled={resolve.isPending}
                  onClick={() => askForApproval(item, "apply")}
                >
                  确认
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={resolve.isPending}
                  onClick={() => askForApproval(item, "ignore")}
                >
                  忽略
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  disabled={resolve.isPending}
                  onClick={() => askForApproval(item, "rollback")}
                >
                  回滚
                </Button>
              </div>
            )}
          </div>
        ))}

        {data && data.recent_actions.length > 0 && (
          <div className="supervision-panel__action-log">
            <div className="supervision-panel__section-title">最近动作</div>
            {data.recent_actions.slice(0, 5).map((action, i) => (
              <div key={i} className="supervision-panel__log-item">
                <span className="supervision-panel__log-time">
                  {new Date(action.timestamp).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                {action.action_type}
                {action.diff_summary && ` — ${action.diff_summary}`}
              </div>
            ))}
          </div>
        )}
      </div>
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
    </aside>
  );
}
