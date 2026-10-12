import type { LabelHTMLAttributes, ReactNode } from "react";
import "./primitives.css";

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
  children: ReactNode;
}

export function Label({
  required = false,
  className = "",
  children,
  ...props
}: LabelProps) {
  const classes = ["label", required ? "label--required" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={classes} {...props}>
      {children}
    </label>
  );
}
