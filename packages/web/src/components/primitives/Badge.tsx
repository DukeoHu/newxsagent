import type { ReactNode } from "react";
import "./primitives.css";

type BadgeVariant = "default" | "accent" | "success" | "warning" | "danger";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  className?: string;
}

export function Badge({
  variant = "default",
  children,
  className = "",
}: BadgeProps) {
  const classes = ["badge", `badge--${variant}`, className]
    .filter(Boolean)
    .join(" ");

  return <span className={classes}>{children}</span>;
}
