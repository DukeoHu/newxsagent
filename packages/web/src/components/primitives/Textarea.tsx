import { forwardRef, type TextareaHTMLAttributes } from "react";
import "./primitives.css";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea({ error, className = "", ...props }, ref) {
    const classes = ["textarea", error ? "textarea--error" : "", className]
      .filter(Boolean)
      .join(" ");

    return (
      <div>
        <textarea ref={ref} className={classes} {...props} />
        {error && <p className="field-error">{error}</p>}
      </div>
    );
  },
);
