import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  CharactersSection,
  TimelineSection,
  WorldSection,
} from "../api/types";
import { Badge, Card } from "../components/primitives";
import "./KnowledgeGraphPage.css";

type GraphNode = { id: string; label: string; type: "character" | "location" | "event" };
type GraphEdge = { source: string; target: string; label: string };

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

export function KnowledgeGraphPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const charactersQuery = useQuery({
    queryKey: ["bible-section", projectId, "characters"],
    queryFn: () => api.getBibleSection(projectId!, "characters"),
    enabled: !!projectId,
  });
  const worldQuery = useQuery({
    queryKey: ["bible-section", projectId, "world"],
    queryFn: () => api.getBibleSection(projectId!, "world"),
    enabled: !!projectId,
  });
  const timelineQuery = useQuery({
    queryKey: ["bible-section", projectId, "timeline"],
    queryFn: () => api.getBibleSection(projectId!, "timeline"),
    enabled: !!projectId,
  });

  const graph = useMemo(() => {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];

    const characters = (charactersQuery.data as CharactersSection | undefined)?.characters ?? [];
    characters.forEach((character, index) => {
      nodes.push({
        id: `c-${index}`,
        label: String(character.name ?? `角色${index + 1}`),
        type: "character",
      });
    });

    const locations = (worldQuery.data as WorldSection | undefined)?.locations ?? [];
    locations.forEach((location, index) => {
      const data = asRecord(location);
      nodes.push({
        id: `l-${index}`,
        label: String(data.name ?? `地点${index + 1}`),
        type: "location",
      });
    });

    const events = (timelineQuery.data as TimelineSection | undefined)?.events ?? [];
    events.forEach((event, index) => {
      const data = asRecord(event);
      nodes.push({
        id: `e-${index}`,
        label: String(data.name ?? data.title ?? `事件${index + 1}`),
        type: "event",
      });
    });

    // 轻量连边策略：角色->事件，事件->地点，保证图谱可视且可读
    const eventNodes = nodes.filter((n) => n.type === "event");
    const characterNodes = nodes.filter((n) => n.type === "character");
    const locationNodes = nodes.filter((n) => n.type === "location");
    eventNodes.forEach((eventNode, idx) => {
      if (characterNodes.length > 0) {
        const character = characterNodes[idx % characterNodes.length];
        edges.push({ source: character.id, target: eventNode.id, label: "参与" });
      }
      if (locationNodes.length > 0) {
        const location = locationNodes[idx % locationNodes.length];
        edges.push({ source: eventNode.id, target: location.id, label: "发生于" });
      }
    });

    return { nodes, edges };
  }, [charactersQuery.data, timelineQuery.data, worldQuery.data]);

  const radius = 180;
  const centerX = 260;
  const centerY = 260;
  const positioned = graph.nodes.map((node, index) => {
    const angle = (index / Math.max(1, graph.nodes.length)) * Math.PI * 2;
    return {
      ...node,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    };
  });
  const nodeMap = new Map(positioned.map((n) => [n.id, n]));

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">知识图谱</h1>
      <p className="page-subtitle">角色、地点、事件的轻量关系可视化</p>

      <div className="knowledge-page__layout">
        <Card padding="md">
          <div className="knowledge-page__legend">
            <Badge variant="accent">角色</Badge>
            <Badge variant="warning">地点</Badge>
            <Badge variant="success">事件</Badge>
          </div>
          <svg className="knowledge-page__canvas" viewBox="0 0 520 520">
            {graph.edges.map((edge, index) => {
              const source = nodeMap.get(edge.source);
              const target = nodeMap.get(edge.target);
              if (!source || !target) return null;
              return (
                <g key={`${edge.source}-${edge.target}-${index}`}>
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#a8a8a4"
                    strokeWidth={1}
                  />
                </g>
              );
            })}
            {positioned.map((node) => {
              const color =
                node.type === "character"
                  ? "#0066FF"
                  : node.type === "location"
                    ? "#D97706"
                    : "#16A34A";
              return (
                <g key={node.id}>
                  <circle cx={node.x} cy={node.y} r={14} fill={color} />
                  <text
                    x={node.x}
                    y={node.y + 30}
                    textAnchor="middle"
                    fill="#1a1a18"
                    style={{ fontSize: "10px" }}
                  >
                    {node.label.slice(0, 8)}
                  </text>
                </g>
              );
            })}
          </svg>
        </Card>

        <Card padding="md" className="knowledge-page__list">
          <h3 style={{ marginBottom: "var(--space-3)" }}>关系明细</h3>
          {graph.edges.length === 0 && <p>暂无可视关系，请先完善角色/地点/事件数据。</p>}
          {graph.edges.map((edge, index) => {
            const s = nodeMap.get(edge.source);
            const t = nodeMap.get(edge.target);
            if (!s || !t) return null;
            return (
              <div key={`${edge.source}-${edge.target}-${index}`} className="knowledge-page__item">
                {s.label} — {edge.label} — {t.label}
              </div>
            );
          })}
        </Card>
      </div>
    </div>
  );
}
