import { forwardRef, type InputHTMLAttributes } from "react";
import "./primitives.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  function Input({ error, className = "", ...props }, ref) {
    const classes = ["input", error ? "input--error" : "", className]
      .filter(Boolean)
      .join(" ");

    return (
      <div>
        <input ref={ref} className={classes} {...props} />
        {error && <p className="field-error">{error}</p>}
      </div>
    );
  },
);
