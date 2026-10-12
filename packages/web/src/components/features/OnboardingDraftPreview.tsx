import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type {
  BibleSectionData,
  BibleSectionName,
  CharacterItem,
  CharactersSection,
  NotesSection,
  PlotSection,
  TimelineSection,
  WorldSection,
} from "../../api/types";
import { CharacterCard } from "./CharacterCard";
import { Badge, Button, Card } from "../primitives";
import "./OnboardingDraftPreview.css";

const SECTION_LABELS: Record<BibleSectionName, string> = {
  characters: "角色",
  plot: "剧情",
  timeline: "时间线",
  world: "世界观",
  notes: "笔记",
};

type ChangeKind = "new" | "replace" | "empty";

function isSectionEmpty(data: BibleSectionData | null | undefined): boolean {
  if (!data) return true;
  if ("characters" in data) return (data.characters?.length ?? 0) === 0;
  if ("acts" in data) {
    return (data.acts?.length ?? 0) === 0 && (data.themes?.length ?? 0) === 0;
  }
  if ("events" in data) return (data.events?.length ?? 0) === 0;
  if ("rules" in data) {
    return (data.rules?.length ?? 0) === 0 && (data.locations?.length ?? 0) === 0;
  }
  if ("style_notes" in data || "style_rules" in data) {
    const notes = data as NotesSection;
    const hasRules = (notes.style_rules?.length ?? 0) > 0;
    return !notes.style_notes?.trim() && !notes.author_notes?.trim() && !hasRules;
  }
  return Object.keys(data).filter((k) => k !== "locked_fields").length === 0;
}

function changeKind(
  current: BibleSectionData | null | undefined,
  draft: BibleSectionData | null | undefined,
): ChangeKind {
  const draftEmpty = isSectionEmpty(draft);
  const currentEmpty = isSectionEmpty(current);
  if (draftEmpty) return "empty";
  if (currentEmpty) return "new";
  return "replace";
}

function ChangeBadge({ kind }: { kind: ChangeKind }) {
  if (kind === "new") return <Badge variant="success">新增</Badge>;
  if (kind === "replace") return <Badge variant="warning">将覆盖</Badge>;
  return null;
}

function labelOf(item: Record<string, unknown>, fallback: string) {
  return String(item.title ?? item.name ?? item.summary ?? fallback);
}

function describe(item: Record<string, unknown>) {
  const text = item.description ?? item.summary ?? item.chapter;
  return text != null ? String(text) : "";
}

function DraftSectionBody({
  section,
  data,
}: {
  section: BibleSectionName;
  data: BibleSectionData;
}) {
  if (section === "characters") {
    const characters = ((data as CharactersSection).characters ?? []) as CharacterItem[];
    if (characters.length === 0) {
      return <p className="onboarding-draft__empty">暂无角色</p>;
    }
    return (
      <div className="onboarding-draft__characters">
        {characters.map((item, index) => (
          <CharacterCard key={`${item.name ?? "char"}-${index}`} character={item} />
        ))}
      </div>
    );
  }

  if (section === "plot") {
    const plot = data as PlotSection;
    return (
      <div className="onboarding-draft__stack">
        {plot.themes?.length > 0 && (
          <div className="onboarding-draft__tags">
            {plot.themes.map((theme) => (
              <Badge key={theme} variant="accent">
                {theme}
              </Badge>
            ))}
          </div>
        )}
        {(plot.acts ?? []).map((act, index) => {
          const record = act as Record<string, unknown>;
          return (
            <div key={String(record.id ?? index)} className="onboarding-draft__item">
              <strong>{labelOf(record, `幕 ${index + 1}`)}</strong>
              {describe(record) && <p>{describe(record)}</p>}
            </div>
          );
        })}
        {(plot.acts ?? []).length === 0 && (
          <p className="onboarding-draft__empty">暂无剧情幕次</p>
        )}
      </div>
    );
  }

  if (section === "world") {
    const world = data as WorldSection;
    return (
      <div className="onboarding-draft__world-grid">
        <div>
          <h4>规则</h4>
          <div className="onboarding-draft__stack">
            {(world.rules ?? []).length === 0 && (
              <p className="onboarding-draft__empty">暂无规则</p>
            )}
            {(world.rules ?? []).map((rule, index) => {
              const record = rule as Record<string, unknown>;
              return (
                <div key={String(record.id ?? index)} className="onboarding-draft__item">
                  <strong>{labelOf(record, `规则 ${index + 1}`)}</strong>
                  {describe(record) && <p>{describe(record)}</p>}
                </div>
              );
            })}
          </div>
        </div>
        <div>
          <h4>地点</h4>
          <div className="onboarding-draft__stack">
            {(world.locations ?? []).length === 0 && (
              <p className="onboarding-draft__empty">暂无地点</p>
            )}
            {(world.locations ?? []).map((loc, index) => {
              const record = loc as Record<string, unknown>;
              return (
                <div key={String(record.id ?? index)} className="onboarding-draft__item">
                  <strong>{labelOf(record, `地点 ${index + 1}`)}</strong>
                  {describe(record) && <p>{describe(record)}</p>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  if (section === "timeline") {
    const timeline = data as TimelineSection;
    return (
      <div className="onboarding-draft__stack">
        {(timeline.events ?? []).length === 0 && (
          <p className="onboarding-draft__empty">暂无事件</p>
        )}
        {(timeline.events ?? []).map((event, index) => {
          const record = event as Record<string, unknown>;
          const chapter = record.chapter ? String(record.chapter) : null;
          return (
            <div key={String(record.id ?? index)} className="onboarding-draft__item">
              <strong>
                {chapter ? `${chapter} · ` : ""}
                {labelOf(record, `事件 ${index + 1}`)}
              </strong>
              {record.summary != null && <p>{String(record.summary)}</p>}
            </div>
          );
        })}
      </div>
    );
  }

  const notes = data as NotesSection;
  const styleRules = notes.style_rules ?? [];
  return (
    <div className="onboarding-draft__stack">
      <div className="onboarding-draft__item">
        <strong>风格摘要</strong>
        <p>{notes.style_notes?.trim() || "暂无"}</p>
      </div>
      <div className="onboarding-draft__item">
        <strong>写作风格规则</strong>
        {styleRules.length === 0 ? (
          <p>暂无</p>
        ) : (
          <div className="onboarding-draft__stack" style={{ marginTop: "var(--space-2)" }}>
            {styleRules.map((rule, index) => (
              <div key={rule.id || index} className="onboarding-draft__item">
                <strong>
                  [{rule.priority || "should"}/{rule.category || "tone"}]{" "}
                  {rule.title || `规则 ${index + 1}`}
                </strong>
                {rule.description && <p>{rule.description}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="onboarding-draft__item">
        <strong>作者笔记</strong>
        <p>{notes.author_notes?.trim() || "暂无"}</p>
      </div>
    </div>
  );
}

interface OnboardingDraftPreviewProps {
  draft: Partial<Record<BibleSectionName, BibleSectionData>>;
  current?: Partial<Record<BibleSectionName, BibleSectionData>> | null;
  applied?: boolean;
  selectedSections?: BibleSectionName[];
  onToggleSection?: (section: BibleSectionName) => void;
}

export function OnboardingDraftPreview({
  draft,
  current,
  applied = false,
  selectedSections,
  onToggleSection,
}: OnboardingDraftPreviewProps) {
  const [showRaw, setShowRaw] = useState(false);
  const sections = (Object.keys(draft) as BibleSectionName[]).filter(
    (key) => draft[key] && !isSectionEmpty(draft[key]),
  );
  const selectable = Boolean(onToggleSection && selectedSections && !applied);

  const summaries = sections.map((section) => ({
    section,
    kind: changeKind(current?.[section], draft[section]),
  }));

  return (
    <div className="onboarding-draft">
      <div className="onboarding-draft__summary">
        {summaries.map(({ section, kind }) => {
          const selected = !selectable || selectedSections!.includes(section);
          return (
            <label
              key={section}
              className={[
                "onboarding-draft__summary-chip",
                selectable ? "onboarding-draft__summary-chip--selectable" : "",
                selectable && !selected
                  ? "onboarding-draft__summary-chip--off"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {selectable && (
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggleSection?.(section)}
                />
              )}
              <span>{SECTION_LABELS[section]}</span>
              <ChangeBadge kind={applied ? "empty" : kind} />
              {applied && <Badge variant="success">已写入</Badge>}
            </label>
          );
        })}
      </div>

      {sections.map((section) => {
        const kind = changeKind(current?.[section], draft[section]);
        const selected = !selectable || selectedSections!.includes(section);
        return (
          <Card
            key={section}
            padding="md"
            className={[
              "onboarding-draft__section",
              selectable && !selected ? "onboarding-draft__section--off" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <div className="onboarding-draft__section-header">
              <div className="onboarding-draft__section-title">
                {selectable && (
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => onToggleSection?.(section)}
                    aria-label={`选择${SECTION_LABELS[section]}`}
                  />
                )}
                <h3>{SECTION_LABELS[section]}</h3>
              </div>
              {!applied && <ChangeBadge kind={kind} />}
            </div>
            <DraftSectionBody section={section} data={draft[section]!} />
          </Card>
        );
      })}

      <div className="onboarding-draft__raw">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowRaw((v) => !v)}
          className="onboarding-draft__raw-toggle"
        >
          {showRaw ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          {showRaw ? "收起原始 JSON" : "查看原始 JSON"}
        </Button>
        {showRaw && (
          <div className="onboarding-draft__diff">
            {sections.map((section) => (
              <Card key={section} padding="md">
                <h4 style={{ marginBottom: "var(--space-3)" }}>
                  {SECTION_LABELS[section]}
                </h4>
                <div className="onboarding-draft__diff-grid">
                  <div>
                    <p className="onboarding-draft__diff-label">当前</p>
                    <pre>{JSON.stringify(current?.[section] ?? {}, null, 2)}</pre>
                  </div>
                  <div>
                    <p className="onboarding-draft__diff-label">草案</p>
                    <pre>{JSON.stringify(draft[section] ?? {}, null, 2)}</pre>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function summarizeDraftChanges(
  draft: Partial<Record<BibleSectionName, BibleSectionData>>,
  current?: Partial<Record<BibleSectionName, BibleSectionData>> | null,
) {
  return (Object.keys(draft) as BibleSectionName[])
    .filter((key) => draft[key] && !isSectionEmpty(draft[key]))
    .map((section) => ({
      section,
      label: SECTION_LABELS[section],
      kind: changeKind(current?.[section], draft[section]),
    }));
}

export function listDraftSections(
  draft: Partial<Record<BibleSectionName, BibleSectionData>>,
): BibleSectionName[] {
  return (Object.keys(draft) as BibleSectionName[]).filter(
    (key) => draft[key] && !isSectionEmpty(draft[key]),
  );
}
