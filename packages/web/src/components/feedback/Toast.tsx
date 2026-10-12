import "./Toast.css";

type ToastType = "success" | "error" | "info";

interface ToastProps {
  message: string;
  type?: ToastType;
}

export function Toast({ message, type = "info" }: ToastProps) {
  return <div className={`toast toast--${type}`}>{message}</div>;
}
