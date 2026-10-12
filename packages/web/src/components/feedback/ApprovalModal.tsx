import { Card, Button } from "../primitives";
import "./ApprovalModal.css";

interface ApprovalModalProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  confirmVariant?: "primary" | "danger";
  loading?: boolean;
  error?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ApprovalModal({
  open,
  title,
  description,
  confirmLabel,
  confirmVariant = "primary",
  loading = false,
  error,
  onConfirm,
  onCancel,
}: ApprovalModalProps) {
  if (!open) return null;

  return (
    <div className="approval-modal__backdrop" role="dialog" aria-modal="true">
      <Card padding="md" className="approval-modal__dialog">
        <h3 className="approval-modal__title">{title}</h3>
        <p className="approval-modal__body">{description}</p>
        {error && <p className="approval-modal__error">{error}</p>}
        <div className="approval-modal__actions">
          <Button variant="ghost" onClick={onCancel} disabled={loading}>
            取消
          </Button>
          <Button variant={confirmVariant} onClick={onConfirm} disabled={loading}>
            {confirmLabel}
          </Button>
        </div>
      </Card>
    </div>
  );
}
