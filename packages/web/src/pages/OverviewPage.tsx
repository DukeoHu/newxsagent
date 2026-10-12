import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  PenLine,
  BookOpen,
  Sparkles,
  Shield,
  Map,
  Gauge,
  Network,
  WandSparkles,
  Settings,
  ScrollText,
  CheckCircle2,
  Circle,
  ArrowRight,
} from "lucide-react";
import { api } from "../api/client";
import { Badge, Button, Card } from "../components/primitives";
import "./OverviewPage.css";

type GuideStep = {
  id: string;
  title: string;
  description: string;
  done: boolean;
  to: string;
  cta: string;
  optional?: boolean;
};

function isLlmReady(mode: string, apiKey: string) {
  if (mode === "simulator" || mode === "ollama") return true;
  if (mode === "deepseek") return apiKey.trim().length > 0;
  return false;
}

export function OverviewPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: status, isLoading } = useQuery({
    queryKey: ["project-status", projectId],
    queryFn: () => api.getProjectStatus(projectId!),
    enabled: !!projectId,
  });

  const { data: llmConfig } = useQuery({
    queryKey: ["llm-config"],
    queryFn: () => api.getLLMConfig(),
  });

  const { data: outlines } = useQuery({
    queryKey: ["outlines", projectId],
    queryFn: () => api.getOutlines(projectId!),
    enabled: !!projectId,
  });

  if (isLoading || !status || !projectId) {
    return <p className="animate-pulse-subtle">加载概览…</p>;
  }

  const healthVariant =
    status.health.overall >= 80
      ? "success"
      : status.health.overall >= 50
        ? "warning"
        : "danger";

  const llmReady = llmConfig
    ? isLlmReady(llmConfig.mode, llmConfig.deepseek_api_key)
    : true;
  const planningReady = (outlines?.chapters.length ?? 0) > 0;
  const writingReady = status.chapter_count > 0;

  const guideSteps: GuideStep[] = [
    {
      id: "llm",
      title: "配置 LLM",
      description: "连接 DeepSeek 或选择模拟器，确保 AI 功能可用",
      done: llmReady,
      to: "/settings/llm",
      cta: "去配置",
      optional: llmConfig?.mode === "simulator",
    },
    {
      id: "onboarding",
      title: "创作引导",
      description: "通过问答生成初始 Story Bible，不要从零手写设定",
      done: status.onboarding_complete,
      to: `/projects/${projectId}/onboarding`,
      cta: status.onboarding_complete ? "查看引导" : "开始引导",
    },
    {
      id: "planning",
      title: "章节规划",
      description: "推导规模并应用章节蓝图，写作前明确每章写什么",
      done: planningReady,
      to: `/projects/${projectId}/planning`,
      cta: "进入规划",
    },
    {
      id: "writing",
      title: "开始写作",
      description: "触发 AI 写作，系统自动同步设定并检测漂移",
      done: writingReady,
      to: `/projects/${projectId}/write`,
      cta: "去写作",
    },
  ];

  const nextStep = guideSteps.find((s) => !s.done && !s.optional) ?? guideSteps.find((s) => !s.done);
  const completedCount = guideSteps.filter((s) => s.done).length;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">{status.name}</h1>
      <p className="page-subtitle">项目概览</p>

      <Card padding="md" className="overview-guide">
        <div className="overview-guide__header">
          <div>
            <h2 className="overview-guide__title">新手路径</h2>
            <p className="overview-guide__subtitle">
              推荐顺序：LLM 配置 → 创作引导 → 章节规划 → 开始写作
            </p>
          </div>
          <Badge variant={completedCount === guideSteps.length ? "success" : "accent"}>
            {completedCount}/{guideSteps.length} 已完成
          </Badge>
        </div>

        <ol className="overview-guide__steps">
          {guideSteps.map((item, index) => (
            <li
              key={item.id}
              className={`overview-guide__step ${item.done ? "overview-guide__step--done" : ""} ${nextStep?.id === item.id ? "overview-guide__step--next" : ""}`}
            >
              <div className="overview-guide__step-icon">
                {item.done ? (
                  <CheckCircle2 size={20} strokeWidth={1.5} />
                ) : (
                  <Circle size={20} strokeWidth={1.5} />
                )}
              </div>
              <div className="overview-guide__step-body">
                <div className="overview-guide__step-title">
                  <span>{index + 1}. {item.title}</span>
                  {item.optional && <Badge>可选</Badge>}
                  {nextStep?.id === item.id && !item.done && (
                    <Badge variant="accent">下一步</Badge>
                  )}
                </div>
                <p>{item.description}</p>
              </div>
              {!item.done && (
                <Link to={item.to} className="overview-guide__step-link">
                  <Button
                    variant={nextStep?.id === item.id ? "primary" : "secondary"}
                    size="sm"
                  >
                    {item.cta}
                    <ArrowRight size={14} strokeWidth={1.5} />
                  </Button>
                </Link>
              )}
            </li>
          ))}
        </ol>

        {nextStep && !nextStep.done && (
          <div className="overview-guide__cta">
            <Link to={nextStep.to}>
              <Button>
                {nextStep.id === "llm" && <Settings size={16} strokeWidth={1.5} />}
                {nextStep.id === "onboarding" && <Sparkles size={16} strokeWidth={1.5} />}
                {nextStep.id === "planning" && <Map size={16} strokeWidth={1.5} />}
                {nextStep.id === "writing" && <PenLine size={16} strokeWidth={1.5} />}
                继续：{nextStep.title}
              </Button>
            </Link>
          </div>
        )}
      </Card>

      <div className="overview-stats">
        <Card padding="md" className="overview-stat">
          <div className="overview-stat__value">{status.chapter_count}</div>
          <div className="overview-stat__label">章节数</div>
        </Card>
        <Card padding="md" className="overview-stat">
          <div className="overview-stat__value">{status.health.overall}</div>
          <div className="overview-stat__label">健康度</div>
        </Card>
        <Card padding="md" className="overview-stat">
          <div className="overview-stat__value">{status.health.pending_count}</div>
          <div className="overview-stat__label">待处理</div>
        </Card>
      </div>

      <Card padding="md">
        <div className="row" style={{ marginBottom: "var(--space-4)" }}>
          <span>状态</span>
          <Badge variant={healthVariant}>整体 {status.health.overall}</Badge>
          <Badge>会话 {status.health.session}</Badge>
          {status.onboarding_complete ? (
            <Badge variant="success">引导已完成</Badge>
          ) : (
            <Badge variant="warning">引导未完成</Badge>
          )}
        </div>

        <div className="overview-actions">
          <Link to={`/projects/${projectId}/write`}>
            <Button>
              <PenLine size={16} strokeWidth={1.5} />
              开始写作
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/bible`}>
            <Button variant="secondary">
              <BookOpen size={16} strokeWidth={1.5} />
              查看设定集
            </Button>
          </Link>
          {!status.onboarding_complete && (
            <Link to={`/projects/${projectId}/onboarding`}>
              <Button variant="secondary">
                <Sparkles size={16} strokeWidth={1.5} />
                完成引导
              </Button>
            </Link>
          )}
          <Link to={`/projects/${projectId}/supervision`}>
            <Button variant="ghost">
              <Shield size={16} strokeWidth={1.5} />
              打开监督页
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/llm-logs`}>
            <Button variant="ghost">
              <ScrollText size={16} strokeWidth={1.5} />
              LLM 调用日志
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/planning`}>
            <Button variant="ghost">
              <Map size={16} strokeWidth={1.5} />
              进入规划页
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/quality`}>
            <Button variant="ghost">
              <Gauge size={16} strokeWidth={1.5} />
              质量仪表盘
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/explore`}>
            <Button variant="ghost">
              <WandSparkles size={16} strokeWidth={1.5} />
              探索采纳
            </Button>
          </Link>
          <Link to={`/projects/${projectId}/knowledge`}>
            <Button variant="ghost">
              <Network size={16} strokeWidth={1.5} />
              知识图谱
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
