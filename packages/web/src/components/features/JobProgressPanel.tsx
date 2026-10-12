import { Badge } from "../primitives";
import "./JobProgressPanel.css";

interface JobProgressPanelProps {
  progress: number;
  events: string[];
}

export function JobProgressPanel({ progress, events }: JobProgressPanelProps) {
  return (
    <div className="job-progress-panel">
      <div className="row">
        <span style={{ fontSize: "var(--text-sm)" }}>任务进度</span>
        <Badge variant={progress === 100 ? "success" : "accent"}>
          {progress}%
        </Badge>
      </div>
      <div className="job-progress-panel__bar">
        <div
          className="job-progress-panel__fill"
          style={{ width: `${progress}%` }}
        />
      </div>
      {events.length > 0 && (
        <div className="job-progress-panel__events">
          {events.map((line, i) => (
            <div key={i} className="job-progress-panel__line">
              {line}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
