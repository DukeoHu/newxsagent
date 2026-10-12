import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  BookOpen,
  Check,
  Loader2,
  MessageCircle,
  MessageSquarePlus,
  RefreshCw,
  RotateCcw,
  Send,
  Sparkles,
} from "lucide-react";
import { api } from "../api/client";
import type {
  BibleSectionData,
  BibleSectionName,
  OnboardingDraftResponse,
  OnboardingTurn,
} from "../api/types";
import {
  OnboardingDraftPreview,
  listDraftSections,
  summarizeDraftChanges,
} from "../components/features";
import { ApprovalModal, Toast } from "../components/feedback";
import { Badge, Button, Card, Textarea } from "../components/primitives";
import "./OnboardingPage.css";

type FlowStep = 1 | 2 | 3 | 4;

const FLOW_STEPS: Array<{ step: FlowStep; label: string }> = [
  { step: 1, label: "聊聊故事" },
  { step: 2, label: "生成设定" },
  { step: 3, label: "确认写入" },
  { step: 4, label: "完成" },
];

const EXAMPLE_PROMPTS = [
  "都市少年收到神秘来信，三幕推进：入局 → 追查 → 对峙真相。开局在废弃邮局。",
  "仙侠复仇线：开局落难，中段结盟，结局打破宗门旧规。主角隐忍冷静，重情义。",
];

export function OnboardingPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatCardRef = useRef<HTMLDivElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  const pendingExampleRef = useRef<string | null>(null);
  const [step, setStep] = useState<FlowStep>(1);
  const [answer, setAnswer] = useState("");
  const [turns, setTurns] = useState<OnboardingTurn[]>([]);
  const [readyToGenerate, setReadyToGenerate] = useState(false);
  const [hint, setHint] = useState<string | null>(null);
  const [generationWarning, setGenerationWarning] = useState<string | null>(null);
  const [draft, setDraft] = useState<OnboardingDraftResponse["draft"] | null>(
    null,
  );
  const [selectedSections, setSelectedSections] = useState<BibleSectionName[]>(
    [],
  );
  const [restartOpen, setRestartOpen] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const sessionQuery = useQuery({
    queryKey: ["onboarding-session", projectId],
    queryFn: () => api.getOnboardingSession(projectId!),
    enabled: !!projectId,
  });

  const currentBibleQuery = useQuery({
    queryKey: ["onboarding-current-bible", projectId],
    queryFn: async () => {
      const sections = await api.listBibleSections(projectId!);
      const entries = await Promise.all(
        sections.map(async (section) => [
          section,
          await api.getBibleSection(projectId!, section),
        ]),
      );
      return Object.fromEntries(entries) as Partial<
        Record<BibleSectionName, BibleSectionData>
      >;
    },
    enabled: !!projectId,
  });

  useEffect(() => {
    const session = sessionQuery.data;
    if (!session) return;
    setTurns(session.turns);
    setReadyToGenerate(
      session.status === "ready" || session.status === "applied",
    );
    const nextDraft = session.draft ?? null;
    setDraft(nextDraft);
    if (nextDraft) {
      setSelectedSections(listDraftSections(nextDraft));
    } else {
      setSelectedSections([]);
    }
    if (session.status === "applied") {
      setStep(4);
    } else if (session.draft) {
      setStep(3);
    } else if (session.status === "ready") {
      setStep(2);
    } else {
      setStep(1);
    }
  }, [sessionQuery.data]);

  const startMutation = useMutation({
    mutationFn: () => api.startOnboarding(projectId!),
    onSuccess: (data) => {
      setTurns(data.session.turns);
      setReadyToGenerate(data.ready_to_generate);
      setHint(data.hint ?? null);
      setGenerationWarning(null);
      setDraft(null);
      setSelectedSections([]);
      setStep(1);
      setRestartOpen(false);
      const seeded = pendingExampleRef.current;
      pendingExampleRef.current = null;
      setAnswer(seeded ?? "");
      queryClient.setQueryData(["onboarding-session", projectId], data.session);
    },
  });

  const answerMutation = useMutation({
    mutationFn: (text: string) => api.answerOnboarding(projectId!, text),
    onSuccess: (data) => {
      setTurns(data.session.turns);
      setReadyToGenerate(data.ready_to_generate);
      setHint(data.hint ?? null);
      setAnswer("");
      if (data.ready_to_generate) {
        setStep(2);
      } else {
        setStep(1);
      }
      queryClient.setQueryData(["onboarding-session", projectId], data.session);
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateOnboarding(projectId!),
    onSuccess: (data) => {
      setDraft(data.draft);
      setSelectedSections(listDraftSections(data.draft));
      setGenerationWarning(data.warning ?? null);
      setStep(3);
      queryClient.setQueryData(
        ["onboarding-session", projectId],
        (prev: typeof sessionQuery.data) =>
          prev ? { ...prev, draft: data.draft, status: "ready" as const } : prev,
      );
      setToast({ type: "success", message: "设定草案已生成，请向下审阅" });
      requestAnimationFrame(() => {
        previewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
    onError: (err: Error) => {
      setToast({ type: "error", message: err.message || "生成失败" });
    },
  });

  const clearDraftMutation = useMutation({
    mutationFn: () => api.clearOnboardingDraft(projectId!),
    onSuccess: (session) => {
      setDraft(null);
      setSelectedSections([]);
      setReadyToGenerate(
        session.status === "ready" || session.status === "applied",
      );
      setStep(session.status === "ready" ? 2 : 1);
      queryClient.setQueryData(["onboarding-session", projectId], session);
      setToast({ type: "success", message: "已返回问答，对话进度已保留" });
      requestAnimationFrame(() => {
        chatCardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
    onError: (err: Error) => {
      setToast({ type: "error", message: err.message || "返回失败" });
    },
  });

  const applyMutation = useMutation({
    mutationFn: (payload: OnboardingDraftResponse["draft"]) =>
      api.applyOnboarding(projectId!, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["onboarding-current-bible", projectId],
      });
      await queryClient.invalidateQueries({ queryKey: ["bible-section", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["project-status", projectId] });
      await queryClient.invalidateQueries({
        queryKey: ["onboarding-session", projectId],
      });
      setStep(4);
      setToast({ type: "success", message: "设定草案已写入设定集" });
    },
    onError: (err: Error) => {
      setToast({ type: "error", message: err.message || "应用失败" });
    },
  });

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, answerMutation.isPending, generateMutation.isPending]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const changeSummary = useMemo(
    () => (draft ? summarizeDraftChanges(draft, currentBibleQuery.data) : []),
    [draft, currentBibleQuery.data],
  );

  const selectedDraft = useMemo(() => {
    if (!draft) return null;
    const payload: OnboardingDraftResponse["draft"] = {};
    for (const section of selectedSections) {
      if (draft[section]) payload[section] = draft[section];
    }
    return payload;
  }, [draft, selectedSections]);

  const userAnswerCount = turns.filter((t) => t.role === "user").length;
  const hasSession = turns.length > 0;
  const isApplied = step === 4;
  const canCompose = hasSession && !isApplied && !draft;
  const canGenerate = readyToGenerate && !isApplied;
  const busy =
    answerMutation.isPending ||
    generateMutation.isPending ||
    applyMutation.isPending ||
    clearDraftMutation.isPending;

  const handleSubmitAnswer = () => {
    const text = answer.trim();
    if (!text || answerMutation.isPending) return;
    answerMutation.mutate(text);
  };

  const handleUseExample = (text: string) => {
    if (hasSession) {
      setAnswer(text);
      return;
    }
    pendingExampleRef.current = text;
    startMutation.mutate();
  };

  const handleToggleSection = (section: BibleSectionName) => {
    setSelectedSections((prev) =>
      prev.includes(section)
        ? prev.filter((item) => item !== section)
        : [...prev, section],
    );
  };

  const handleApply = () => {
    if (!selectedDraft || selectedSections.length === 0) {
      setToast({ type: "error", message: "请至少勾选一个分区再写入" });
      return;
    }
    applyMutation.mutate(selectedDraft);
  };

  if (!projectId) return null;

  return (
    <div className="animate-fade-in onboarding-page">
      <h1 className="page-title">创作引导</h1>
      <p className="page-subtitle">
        通过对话收集灵感，生成可读的初始设定，再一键写入设定集
      </p>

      <ol className="onboarding-page__steps">
        {FLOW_STEPS.map((item, index) => {
          const done = step > item.step || (item.step === 4 && step === 4);
          const current = step === item.step && step < 4;
          return (
            <li
              key={item.step}
              className={[
                "onboarding-page__step",
                done ? "onboarding-page__step--done" : "",
                current ? "onboarding-page__step--current" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <span className="onboarding-page__step-index">
                {done ? <Check size={14} strokeWidth={2} /> : item.step}
              </span>
              <span className="onboarding-page__step-label">{item.label}</span>
              {index < FLOW_STEPS.length - 1 && (
                <span className="onboarding-page__step-connector" aria-hidden />
              )}
            </li>
          );
        })}
      </ol>

      <div className="onboarding-page__layout">
        <div ref={chatCardRef} className="onboarding-page__chat-wrap">
        <Card padding="md" className="onboarding-page__chat">
          <div className="onboarding-page__chat-header">
            <MessageCircle size={18} strokeWidth={1.5} />
            <span>引导对话</span>
            {hasSession && (
              <Button
                variant="ghost"
                className="onboarding-page__restart"
                onClick={() => setRestartOpen(true)}
                disabled={startMutation.isPending}
              >
                <RotateCcw size={14} strokeWidth={1.5} />
                重新开始
              </Button>
            )}
          </div>

          {!hasSession ? (
            <div className="onboarding-page__empty">
              <p>
                首轮请描述整体故事与结构，随后会追问主角、世界观、冲突与风格等细节。
              </p>
              <div className="onboarding-page__examples">
                <p className="onboarding-page__examples-title">点选示例开始：</p>
                <div className="onboarding-page__example-actions">
                  {EXAMPLE_PROMPTS.map((text) => (
                    <button
                      key={text}
                      type="button"
                      className="onboarding-page__example-chip"
                      disabled={startMutation.isPending}
                      onClick={() => handleUseExample(text)}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
              <p className="onboarding-page__empty-hint">
                建议先完成侧栏底部的 LLM 配置，再开始问答。
              </p>
              <Button
                onClick={() => startMutation.mutate()}
                disabled={startMutation.isPending}
              >
                {startMutation.isPending ? (
                  <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
                ) : (
                  <Sparkles size={16} strokeWidth={1.5} />
                )}
                开始引导问答
              </Button>
            </div>
          ) : (
            <div className="onboarding-page__messages">
              {turns.map((turn, index) => (
                <div
                  key={`${turn.role}-${index}`}
                  className={`onboarding-page__bubble onboarding-page__bubble--${turn.role}`}
                >
                  <span className="onboarding-page__bubble-label">
                    {turn.role === "assistant" ? "引导师" : "你"}
                  </span>
                  <p>{turn.content}</p>
                </div>
              ))}
              {answerMutation.isPending && (
                <div className="onboarding-page__bubble onboarding-page__bubble--assistant onboarding-page__bubble--thinking">
                  <span className="onboarding-page__bubble-label">引导师</span>
                  <p className="onboarding-page__thinking">
                    <Loader2 size={14} className="animate-spin" />
                    正在思考下一问…
                  </p>
                </div>
              )}
              {generateMutation.isPending && (
                <div className="onboarding-page__bubble onboarding-page__bubble--assistant onboarding-page__bubble--thinking">
                  <span className="onboarding-page__bubble-label">引导师</span>
                  <p className="onboarding-page__thinking">
                    <Loader2 size={14} className="animate-spin" />
                    正在根据对话整理设定草案…
                  </p>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}

          {canCompose && (
            <div className="onboarding-page__composer">
              {hint && <p className="onboarding-page__hint">{hint}</p>}
              {readyToGenerate && (
                <p className="onboarding-page__hint">
                  已可生成草案；若还想补充细节，可继续发送后再生成。
                </p>
              )}
              <div className="onboarding-page__composer-row">
                <Textarea
                  className="onboarding-page__input"
                  rows={3}
                  placeholder="输入你的回答…"
                  value={answer}
                  disabled={answerMutation.isPending || generateMutation.isPending}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmitAnswer();
                    }
                  }}
                />
                <Button
                  onClick={handleSubmitAnswer}
                  disabled={
                    !answer.trim() ||
                    answerMutation.isPending ||
                    generateMutation.isPending
                  }
                >
                  {answerMutation.isPending ? (
                    <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
                  ) : (
                    <Send size={16} strokeWidth={1.5} />
                  )}
                  发送
                </Button>
              </div>
            </div>
          )}

          {canGenerate && !draft && (
            <div className="onboarding-page__generate">
              <p>信息已收集充分，可以生成 Story Bible 草案。</p>
              <Button
                onClick={() => {
                  setStep(2);
                  generateMutation.mutate();
                }}
                disabled={generateMutation.isPending || answerMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
                ) : (
                  <Sparkles size={16} strokeWidth={1.5} />
                )}
                {generateMutation.isPending ? "生成中…" : "生成设定草案"}
              </Button>
            </div>
          )}

          {generationWarning && (
            <Badge variant="warning" className="onboarding-page__error">
              {generationWarning}
            </Badge>
          )}

          {(startMutation.isError ||
            answerMutation.isError ||
            generateMutation.isError) && (
            <Badge variant="danger" className="onboarding-page__error">
              {(
                (startMutation.error ||
                  answerMutation.error ||
                  generateMutation.error) as Error
              ).message}
            </Badge>
          )}
        </Card>
        </div>

        <Card padding="md" className="onboarding-page__sidebar">
          <h3>当前进度</h3>
          {step === 1 && (
            <div className="onboarding-page__context">
              <p>
                已回答 <strong>{userAnswerCount}</strong> 轮
                {userAnswerCount < 3
                  ? `，建议至少再补充 ${3 - userAnswerCount} 轮细节`
                  : "，也可继续补充到最多 6 轮"}
                。
              </p>
              <p className="onboarding-page__context-tip">
                {hint ||
                  "越具体越好：主角动机、核心冲突、世界观规则、开篇场景。"}
              </p>
            </div>
          )}
          {step === 2 && !draft && (
            <div className="onboarding-page__context">
              <p>准备把对话整理成角色、剧情、世界观等初始设定。</p>
              {generateMutation.isPending ? (
                <p className="onboarding-page__context-tip onboarding-page__thinking">
                  <Loader2 size={14} className="animate-spin" />
                  生成中，通常需要几秒到十几秒。
                </p>
              ) : (
                <p className="onboarding-page__context-tip">
                  点击「生成设定草案」后，可在下方审阅再决定是否写入。
                </p>
              )}
            </div>
          )}
          {(step === 3 || (step === 2 && draft)) && draft && !isApplied && (
            <div className="onboarding-page__context">
              <p>
                勾选要写入的分区。不满意可重新生成，或返回补充问答（对话保留）。
              </p>
              <ul className="onboarding-page__change-list">
                {changeSummary.map((item) => {
                  const selected = selectedSections.includes(item.section);
                  return (
                    <li key={item.section} className={!selected ? "is-off" : undefined}>
                      <label className="onboarding-page__change-label">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => handleToggleSection(item.section)}
                        />
                        <span>{item.label}</span>
                      </label>
                      {item.kind === "new" && <Badge variant="success">新增</Badge>}
                      {item.kind === "replace" && (
                        <Badge variant="warning">将覆盖</Badge>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          {step === 4 && (
            <div className="onboarding-page__done">
              <Badge variant="success">引导已完成</Badge>
              <p>设定已写入。下一步去规划章节蓝图，再开始写作。</p>
              <div className="onboarding-page__done-actions">
                <Link to={`/projects/${projectId}/planning`}>
                  <Button variant="secondary">前往规划</Button>
                </Link>
                <Link to={`/projects/${projectId}/bible`}>
                  <Button variant="ghost">
                    <BookOpen size={14} strokeWidth={1.5} />
                    查看设定集
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>

      {draft && step >= 3 && (
        <div ref={previewRef} className="onboarding-page__preview">
          <div className="onboarding-page__preview-header">
            <h2>设定草案预览</h2>
            <p>
              {isApplied
                ? "以下为已写入的设定摘要。"
                : "勾选要写入的分区；默认全选。可展开原始 JSON 核对细节。"}
            </p>
          </div>
          <OnboardingDraftPreview
            draft={draft}
            current={currentBibleQuery.data}
            applied={isApplied}
            selectedSections={selectedSections}
            onToggleSection={isApplied ? undefined : handleToggleSection}
          />
          <Card padding="md" className="onboarding-page__apply-bar">
            <div className="onboarding-page__apply-row">
              {!isApplied && (
                <>
                  <Button
                    variant="primary"
                    onClick={handleApply}
                    disabled={busy || selectedSections.length === 0}
                  >
                    {applyMutation.isPending ? (
                      <Loader2
                        size={16}
                        className="animate-spin"
                        strokeWidth={1.5}
                      />
                    ) : null}
                    {applyMutation.isPending
                      ? "写入中…"
                      : selectedSections.length === 0
                        ? "请先勾选分区"
                        : `写入所选分区（${selectedSections.length}）`}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => generateMutation.mutate()}
                    disabled={busy}
                  >
                    {generateMutation.isPending ? (
                      <Loader2
                        size={16}
                        className="animate-spin"
                        strokeWidth={1.5}
                      />
                    ) : (
                      <RefreshCw size={16} strokeWidth={1.5} />
                    )}
                    {generateMutation.isPending ? "重新生成中…" : "重新生成"}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => clearDraftMutation.mutate()}
                    disabled={busy}
                  >
                    {clearDraftMutation.isPending ? (
                      <Loader2
                        size={16}
                        className="animate-spin"
                        strokeWidth={1.5}
                      />
                    ) : (
                      <MessageSquarePlus size={16} strokeWidth={1.5} />
                    )}
                    返回补充问答
                  </Button>
                </>
              )}
              {isApplied && (
                <>
                  <Badge variant="success">已应用到设定集</Badge>
                  <Link to={`/projects/${projectId}/bible`}>
                    <Button variant="secondary">
                      <BookOpen size={16} strokeWidth={1.5} />
                      打开设定集
                    </Button>
                  </Link>
                  <Link to={`/projects/${projectId}/planning`}>
                    <Button>前往规划</Button>
                  </Link>
                </>
              )}
              {applyMutation.isError && (
                <Badge variant="danger">
                  {(applyMutation.error as Error).message}
                </Badge>
              )}
            </div>
          </Card>
        </div>
      )}

      <ApprovalModal
        open={restartOpen}
        title="重新开始引导？"
        description={
          isApplied
            ? "将开启新的问答会话。已写入设定集的内容不会自动回滚，如需修改请之后在设定集中编辑。"
            : "当前对话进度将被清空，需要重新回答引导问题。"
        }
        confirmLabel="重新开始"
        confirmVariant="danger"
        loading={startMutation.isPending}
        error={
          startMutation.isError
            ? (startMutation.error as Error).message
            : undefined
        }
        onConfirm={() => startMutation.mutate()}
        onCancel={() => setRestartOpen(false)}
      />

      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
}
