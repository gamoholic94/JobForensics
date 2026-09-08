import * as React from "react";
import { cn } from "@/lib/utils";

export function Button({
  className,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}) {
  const variants = {
    primary: "bg-[#315fce] text-white hover:bg-[#2854ba]",
    secondary: "border border-[var(--border)] bg-[var(--card)] hover:bg-black/[.03] dark:hover:bg-white/[.04]",
    ghost: "hover:bg-black/[.04] dark:hover:bg-white/[.05]",
    danger: "bg-[#f04438] text-white hover:bg-[#d92d20]",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
