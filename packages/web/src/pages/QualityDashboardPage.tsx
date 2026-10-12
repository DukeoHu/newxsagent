import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { Badge, Card } from "../components/primitives";
import "./QualityDashboardPage.css";

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value));
}

export function QualityDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const statusQuery = useQuery({
    queryKey: ["project-status", projectId],
    queryFn: () => api.getProjectStatus(projectId!),
    enabled: !!projectId,
  });
  const supervisionQuery = useQuery({
    queryKey: ["supervision", projectId],
    queryFn: () => api.getSupervision(projectId!),
    enabled: !!projectId,
  });
  const outlinesQuery = useQuery({
    queryKey: ["outlines", projectId],
    queryFn: () => api.getOutlines(projectId!),
    enabled: !!projectId,
  });
  const chaptersQuery = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => api.listChapters(projectId!),
    enabled: !!projectId,
  });

  const chapterCount = chaptersQuery.data?.length ?? 0;
  const chapterWords = (chaptersQuery.data ?? []).reduce(
    (sum, chapter) => sum + chapter.word_count,
    0,
  );
  const avgChapterWords = chapterCount > 0 ? Math.round(chapterWords / chapterCount) : 0;
  const planningCompletion = clampPercent(outlinesQuery.data?.completion ?? 0);
  const healthOverall = clampPercent(statusQuery.data?.health.overall ?? 0);
  const healthSession = clampPercent(statusQuery.data?.health.session ?? 0);
  const pendingCount = supervisionQuery.data?.pending_items.length ?? 0;
  const highRiskCount =
    supervisionQuery.data?.pending_items.filter((item) => item.risk_level === "high")
      .length ?? 0;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">质量仪表盘</h1>
      <p className="page-subtitle">关键质量指标总览（健康度、规划完成度、风险负载）</p>

      <div className="quality-page__stats">
        <Card padding="md">
          <div className="quality-page__stat-value">{chapterCount}</div>
          <div className="quality-page__stat-label">章节数</div>
        </Card>
        <Card padding="md">
          <div className="quality-page__stat-value">{avgChapterWords}</div>
          <div className="quality-page__stat-label">章均字数</div>
        </Card>
        <Card padding="md">
          <div className="quality-page__stat-value">{pendingCount}</div>
          <div className="quality-page__stat-label">待处理事项</div>
        </Card>
        <Card padding="md">
          <div className="quality-page__stat-value">{highRiskCount}</div>
          <div className="quality-page__stat-label">高风险事项</div>
        </Card>
      </div>

      <div className="quality-page__bars">
        <Card padding="md">
          <div className="quality-page__bar-title">整体健康度</div>
          <div className="quality-page__bar-track">
            <div className="quality-page__bar-fill" style={{ width: `${healthOverall}%` }} />
          </div>
          <div className="quality-page__bar-value">{healthOverall.toFixed(1)}%</div>
        </Card>

        <Card padding="md">
          <div className="quality-page__bar-title">会话健康度</div>
          <div className="quality-page__bar-track">
            <div className="quality-page__bar-fill" style={{ width: `${healthSession}%` }} />
          </div>
          <div className="quality-page__bar-value">{healthSession.toFixed(1)}%</div>
        </Card>

        <Card padding="md">
          <div className="quality-page__bar-title">规划完成度</div>
          <div className="quality-page__bar-track">
            <div
              className="quality-page__bar-fill"
              style={{ width: `${planningCompletion}%` }}
            />
          </div>
          <div className="quality-page__bar-value">
            {planningCompletion.toFixed(1)}%
          </div>
        </Card>

        <Card padding="md">
          <div className="quality-page__bar-title">风险负载</div>
          <div className="row" style={{ marginBottom: "var(--space-2)" }}>
            <Badge variant={highRiskCount > 0 ? "danger" : "success"}>
              高风险 {highRiskCount}
            </Badge>
            <Badge variant={pendingCount > 0 ? "warning" : "success"}>
              总待办 {pendingCount}
            </Badge>
          </div>
          <div className="quality-page__bar-value">
            建议维持高风险事项为 0，待办总量逐步下降
          </div>
        </Card>
      </div>
    </div>
  );
}
