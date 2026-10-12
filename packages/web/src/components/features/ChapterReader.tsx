import type { Chapter } from "../../api/types";
import { Badge, Card } from "../primitives";
import "./ChapterReader.css";

interface ChapterReaderProps {
  chapter: Chapter;
}

export function ChapterReader({ chapter }: ChapterReaderProps) {
  return (
    <Card padding="lg">
      <h2 className="chapter-reader__title">{chapter.title}</h2>
      <div className="chapter-reader__content">{chapter.content_md}</div>
      <div className="row" style={{ marginTop: "var(--space-6)" }}>
        <Badge>{chapter.id}</Badge>
        <Badge variant="default">{chapter.word_count} 字</Badge>
      </div>
    </Card>
  );
}
