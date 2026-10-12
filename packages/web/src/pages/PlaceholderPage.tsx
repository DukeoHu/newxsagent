import { useParams } from "react-router-dom";

interface PlaceholderPageProps {
  title: string;
  description?: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">{title}</h1>
      <p className="page-subtitle">
        {description ?? `项目 ${projectId} — 此页面将在后续阶段实现`}
      </p>
    </div>
  );
}
