import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { api } from "../api/client";
import type { Project } from "../api/types";
import { AppShell } from "../components/layout/AppShell";
import { ApprovalModal, Toast } from "../components/feedback";
import { Badge, Button, Card, Input, Label } from "../components/primitives";
import "./HomePage.css";

export function HomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("玄幻");
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  const create = useMutation({
    mutationFn: () => api.createProject({ name: title, genre }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate(`/projects/${project.id}`);
    },
    onError: (err: Error) => setError(err.message),
  });

  const deleteProject = useMutation({
    mutationFn: (projectId: string) => api.deleteProject(projectId),
    onSuccess: async (_data, projectId) => {
      queryClient.removeQueries({ queryKey: ["project-status", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      setDeleteTarget(null);
      setDeleteError("");
      setToast({ message: "项目已删除", type: "success" });
    },
    onError: (err: Error) => {
      const message =
        err.message === "Method Not Allowed"
          ? "删除接口未生效，请重启后端服务（python -m xsagent）后重试"
          : err.message || "删除失败";
      setDeleteError(message);
      setToast({ message, type: "error" });
    },
  });

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!title.trim()) {
      setError("请输入项目名称");
      return;
    }
    create.mutate();
  };

  return (
    <AppShell centered>
      <div className="home-page__header animate-fade-in">
        <h1 className="page-title">项目</h1>
        <p className="page-subtitle">管理你的长篇小说创作项目</p>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus size={16} strokeWidth={1.5} />
          新建项目
        </Button>
      </div>

      {showCreate && (
        <Card padding="md" className="animate-fade-in" style={{ marginBottom: "var(--space-8)" }}>
          <form className="home-page__create-form" onSubmit={handleCreate}>
            <div>
              <Label htmlFor="title" required>
                项目名称
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="例如：星辰之约"
              />
            </div>
            <div>
              <Label htmlFor="genre" required>
                类型
              </Label>
              <Input
                id="genre"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                placeholder="玄幻、科幻、都市…"
              />
            </div>
            {error && <p className="home-page__error">{error}</p>}
            <div className="row">
              <Button type="submit" disabled={create.isPending}>
                {create.isPending && (
                  <Loader2 size={16} className="animate-spin" strokeWidth={1.5} />
                )}
                创建
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowCreate(false)}
              >
                取消
              </Button>
            </div>
          </form>
        </Card>
      )}

      {isLoading && (
        <p className="home-page__empty animate-pulse-subtle">加载项目列表…</p>
      )}

      {!isLoading && projects?.length === 0 && !showCreate && (
        <Card padding="lg" className="home-page__empty">
          <p>还没有项目，点击上方按钮开始创作。</p>
        </Card>
      )}

      {projects && projects.length > 0 && (
        <div className="home-page__grid animate-fade-in">
          {projects.map((p) => (
            <Card
              key={p.id}
              interactive
              padding="md"
              className="home-page__project-card"
              onClick={() => navigate(`/projects/${p.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  navigate(`/projects/${p.id}`);
                }
              }}
            >
              <div className="home-page__project-top">
                <h3 className="home-page__project-title">{p.name}</h3>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="home-page__delete-btn"
                  aria-label={`删除项目 ${p.name}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteError("");
                    setDeleteTarget(p);
                  }}
                >
                  <Trash2 size={16} strokeWidth={1.5} />
                </Button>
              </div>
              <p className="home-page__project-genre">{p.genre}</p>
              <div className="home-page__project-meta">
                <Badge>{p.id.slice(0, 8)}</Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ApprovalModal
        open={!!deleteTarget}
        title="删除项目"
        description={`确定删除「${deleteTarget?.name ?? ""}」吗？项目目录、章节、设定与大纲将被永久移除，且无法恢复。`}
        confirmLabel="确认删除"
        confirmVariant="danger"
        loading={deleteProject.isPending}
        error={deleteError}
        onConfirm={() => {
          if (!deleteTarget) return;
          deleteProject.mutate(deleteTarget.id);
        }}
        onCancel={() => {
          setDeleteTarget(null);
          setDeleteError("");
        }}
      />

      {toast && <Toast message={toast.message} type={toast.type} />}
    </AppShell>
  );
}
