import "./MarkdownView.css";

interface MarkdownViewProps {
  content: string;
}

function simpleMarkdownToText(content: string): string {
  return content
    .replace(/^###\s+/gm, "")
    .replace(/^##\s+/gm, "")
    .replace(/^#\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .trim();
}

export function MarkdownView({ content }: MarkdownViewProps) {
  if (!content.trim()) {
    return <p className="markdown-view">暂无内容</p>;
  }

  return <div className="markdown-view">{simpleMarkdownToText(content)}</div>;
}
