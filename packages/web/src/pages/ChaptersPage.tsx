import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { RotateCcw, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { ChapterReader } from "../components/features";
import { ApprovalModal, Toast } from "../components/feedback";
import { Badge, Button, Card } from "../components/primitives";
import "./ChaptersPage.css";

export function ChaptersPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeChapterId, setActiveChapterId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const chaptersQuery = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => api.listChapters(projectId!),
    enabled: !!projectId,
  });

  const chapterQuery = useQuery({
    queryKey: ["chapter", projectId, activeChapterId],
    queryFn: () => api.getChapter(projectId!, activeChapterId!),
    enabled: !!projectId && !!activeChapterId,
  });

  const deleteChapter = useMutation({
    mutationFn: (chapterId: string) => api.deleteChapter(projectId!, chapterId),
    onSuccess: async (_data, chapterId) => {
      queryClient.removeQueries({ queryKey: ["chapter", projectId, chapterId] });
      const updated = await queryClient.fetchQuery({
        queryKey: ["chapters", projectId],
        queryFn: () => api.listChapters(projectId!),
      });
      queryClient.invalidateQueries({ queryKey: ["project-status", projectId] });
      const nextId = updated.find((item) => item.id !== chapterId)?.id ?? null;
      setActiveChapterId(nextId);
      setDeleteConfirm(false);
      setDeleteError("");
      setToast({ message: "章节已删除", type: "success" });
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
    if (!activeChapterId && chaptersQuery.data && chaptersQuery.data.length > 0) {
      setActiveChapterId(chaptersQuery.data[0].id);
    }
  }, [activeChapterId, chaptersQuery.data]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleRewrite = () => {
    if (!projectId || !activeChapterId) return;
    navigate(`/projects/${projectId}/write?chapter_id=${activeChapterId}`);
  };

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">章节</h1>
      <p className="page-subtitle">章节列表与内容阅读</p>

      <div className="chapters-page__layout">
        <Card padding="md" className="chapters-page__list">
          {chaptersQuery.isLoading && (
            <p className="animate-pulse-subtle">加载章节列表…</p>
          )}
          {!chaptersQuery.isLoading &&
            (chaptersQuery.data?.length ?? 0) === 0 && (
              <p>暂无章节，请先去写作页生成章节。</p>
            )}
          {chaptersQuery.data?.map((chapter) => (
            <Button
              key={chapter.id}
              variant={activeChapterId === chapter.id ? "primary" : "secondary"}
              className="chapters-page__item"
              onClick={() => setActiveChapterId(chapter.id)}
            >
              <div className="chapters-page__item-title">{chapter.title}</div>
              <div className="chapters-page__item-meta">
                {chapter.id} · {chapter.word_count} 字
              </div>
            </Button>
          ))}
        </Card>

        <div>
          {chapterQuery.isLoading && (
            <Card padding="md">
              <p className="animate-pulse-subtle">加载章节内容…</p>
            </Card>
          )}
          {chapterQuery.data ? (
            <>
              <Card padding="md" className="chapters-page__actions">
                <div className="row">
                  <Badge>{chapterQuery.data.id}</Badge>
                  <Badge>{chapterQuery.data.word_count} 字</Badge>
                </div>
                <div className="row chapters-page__action-buttons">
                  <Button variant="secondary" onClick={handleRewrite}>
                    <RotateCcw size={16} strokeWidth={1.5} />
                    重写本章
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => {
                      setDeleteError("");
                      setDeleteConfirm(true);
                    }}
                  >
                    <Trash2 size={16} strokeWidth={1.5} />
                    删除章节
                  </Button>
                </div>
              </Card>
              <ChapterReader chapter={chapterQuery.data} />
            </>
          ) : (
            <Card padding="md">
              <div className="row">
                <Badge>未选择章节</Badge>
              </div>
            </Card>
          )}
        </div>
      </div>

      <ApprovalModal
        open={deleteConfirm}
        title="删除章节"
        description={`确定删除 ${activeChapterId ?? ""} 吗？章节正文将被移除，关联蓝图会标记为待写。`}
        confirmLabel="确认删除"
        confirmVariant="danger"
        loading={deleteChapter.isPending}
        error={deleteError}
        onConfirm={() => {
          if (!activeChapterId) return;
          deleteChapter.mutate(activeChapterId);
        }}
        onCancel={() => {
          setDeleteConfirm(false);
          setDeleteError("");
        }}
      />

      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  );
}
