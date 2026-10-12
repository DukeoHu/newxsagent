import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Save } from "lucide-react";
import { api } from "../api/client";
import type {
  BibleSectionData,
  BibleSectionName,
  CharacterItem,
  CharactersSection,
  NotesSection,
  PlotSection,
  TimelineSection,
  WorldSection,
} from "../api/types";
import { CharacterCard, ForeshadowingBoard, MarkdownView } from "../components/features";
import { Badge, Button, Card, Textarea } from "../components/primitives";
import "./BiblePage.css";

const SECTION_LABELS: Record<BibleSectionName, string> = {
  characters: "角色",
  plot: "剧情",
  timeline: "时间线",
  world: "世界观",
  notes: "笔记",
};

function asArrayString(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item));
}

function toPrettyJson(data: BibleSectionData | null): string {
  return JSON.stringify(data ?? {}, null, 2);
}

function getLockedCount(data: BibleSectionData | null): number {
  if (!data) return 0;
  return Array.isArray(data.locked_fields) ? data.locked_fields.length : 0;
}

export function BiblePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeSection, setActiveSection] = useState<BibleSectionName>("characters");
  const [editorValue, setEditorValue] = useState("");

  const { data: sections } = useQuery({
    queryKey: ["bible-sections", projectId],
    queryFn: () => api.listBibleSections(projectId!),
    enabled: !!projectId,
  });

  const sectionQuery = useQuery({
    queryKey: ["bible-section", projectId, activeSection],
    queryFn: () => api.getBibleSection(projectId!, activeSection),
    enabled: !!projectId,
  });

  const saveMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.putBibleSection(projectId!, activeSection, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["bible-section", projectId, activeSection],
      });
    },
  });

  const data = (sectionQuery.data ?? null) as BibleSectionData | null;

  useEffect(() => {
    setEditorValue(toPrettyJson(data));
  }, [data]);

  const characters = ((data as CharactersSection | null)?.characters ??
    []) as CharacterItem[];
  const notes = (data as NotesSection | null) ?? null;
  const world = (data as WorldSection | null) ?? null;
  const timeline = (data as TimelineSection | null) ?? null;
  const plot = (data as PlotSection | null) ?? null;

  const setup = asArrayString((plot?.acts?.[0] as Record<string, unknown> | undefined)?.setup);
  const progress = asArrayString(
    (plot?.acts?.[1] as Record<string, unknown> | undefined)?.progress,
  );
  const payoff = asArrayString(
    (plot?.acts?.[2] as Record<string, unknown> | undefined)?.payoff,
  );

  const saveSection = () => {
    try {
      const parsed = JSON.parse(editorValue) as Record<string, unknown>;
      saveMutation.mutate(parsed);
    } catch {
      // ignore parse errors; the error message is handled in UI
    }
  };

  const parseError = (() => {
    try {
      JSON.parse(editorValue);
      return "";
    } catch (err) {
      return err instanceof Error ? err.message : "JSON 格式错误";
    }
  })();

  if (!projectId) return null;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">设定集</h1>
      <p className="page-subtitle">角色、剧情、世界观与创作笔记的统一管理视图</p>

      <div className="bible-page__section-tabs">
        {(sections ?? (Object.keys(SECTION_LABELS) as BibleSectionName[])).map(
          (section) => (
            <Button
              key={section}
              variant={activeSection === section ? "primary" : "secondary"}
              size="sm"
              onClick={() => setActiveSection(section)}
            >
              {SECTION_LABELS[section]}
            </Button>
          ),
        )}
      </div>

      <div className="bible-page__toolbar">
        <div className="row">
          <Badge variant="accent">当前分区：{SECTION_LABELS[activeSection]}</Badge>
          {data && (
            <Badge>锁字段 {getLockedCount(data)}</Badge>
          )}
        </div>
        <Button
          variant="primary"
          onClick={saveSection}
          disabled={!!parseError || saveMutation.isPending}
        >
          <Save size={16} strokeWidth={1.5} />
          保存分区
        </Button>
      </div>

      {activeSection === "characters" && (
        <div className="bible-page__characters">
          {characters.length === 0 && <Card>暂无角色，请在下方 JSON 编辑器补充。</Card>}
          {characters.map((item, index) => (
            <CharacterCard key={`${item.name ?? "unknown"}-${index}`} character={item} />
          ))}
        </div>
      )}

      {activeSection === "plot" && (
        <Card padding="md" style={{ marginBottom: "var(--space-6)" }}>
          <h3 style={{ marginBottom: "var(--space-3)" }}>伏笔看板</h3>
          <ForeshadowingBoard setup={setup} progress={progress} payoff={payoff} />
        </Card>
      )}

      {activeSection === "notes" && notes && (
        <div className="stack" style={{ marginBottom: "var(--space-6)" }}>
          <Card padding="md">
            <h3 style={{ marginBottom: "var(--space-3)" }}>风格摘要</h3>
            <MarkdownView content={notes.style_notes} />
          </Card>
          <Card padding="md">
            <h3 style={{ marginBottom: "var(--space-3)" }}>写作风格规则</h3>
            {(notes.style_rules?.length ?? 0) === 0 ? (
              <p style={{ color: "var(--color-text-muted)" }}>暂无风格规则</p>
            ) : (
              <div className="bible-page__world-list">
                {notes.style_rules!.map((rule, index) => (
                  <div key={rule.id || index} className="bible-page__world-list-item">
                    <strong>
                      [{rule.priority}/{rule.category}] {rule.title}
                    </strong>
                    {rule.description && <p style={{ marginTop: "var(--space-1)" }}>{rule.description}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>
          <Card padding="md">
            <h3 style={{ marginBottom: "var(--space-3)" }}>作者笔记</h3>
            <MarkdownView content={notes.author_notes} />
          </Card>
        </div>
      )}

      {activeSection === "world" && world && (
        <div className="bible-page__world-grid" style={{ marginBottom: "var(--space-6)" }}>
          <Card padding="md">
            <h3>规则</h3>
            <div className="bible-page__world-list">
              {world.rules.length === 0 && <div className="bible-page__world-list-item">暂无规则</div>}
              {world.rules.map((item, index) => (
                <div key={index} className="bible-page__world-list-item">
                  {JSON.stringify(item)}
                </div>
              ))}
            </div>
          </Card>
          <Card padding="md">
            <h3>地点</h3>
            <div className="bible-page__world-list">
              {world.locations.length === 0 && (
                <div className="bible-page__world-list-item">暂无地点</div>
              )}
              {world.locations.map((item, index) => (
                <div key={index} className="bible-page__world-list-item">
                  {JSON.stringify(item)}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeSection === "timeline" && timeline && (
        <Card padding="md" style={{ marginBottom: "var(--space-6)" }}>
          <h3 style={{ marginBottom: "var(--space-3)" }}>时间线事件</h3>
          <div className="bible-page__world-list">
            {timeline.events.length === 0 && <div className="bible-page__world-list-item">暂无事件</div>}
            {timeline.events.map((event, index) => (
              <div key={index} className="bible-page__world-list-item">
                {JSON.stringify(event)}
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card padding="md" className="bible-page__editor">
        <h3 style={{ marginBottom: "var(--space-3)" }}>JSON 编辑器</h3>
        <Textarea
          value={editorValue}
          onChange={(e) => setEditorValue(e.target.value)}
          rows={18}
          error={parseError || undefined}
        />
      </Card>
    </div>
  );
}
