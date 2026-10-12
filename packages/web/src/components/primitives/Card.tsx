import type { HTMLAttributes, ReactNode } from "react";
import "./primitives.css";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: "sm" | "md" | "lg";
  interactive?: boolean;
  children: ReactNode;
}

export function Card({
  padding = "md",
  interactive = false,
  className = "",
  children,
  ...props
}: CardProps) {
  const classes = [
    "card",
    `card--padding-${padding}`,
    interactive ? "card--interactive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}
