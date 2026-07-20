import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline";
}

export function Button({
  children,
  className = "",
  variant = "default",
  ...props
}: ButtonProps) {
  const base =
    "px-4 py-2 rounded-lg transition-all duration-200";

  const styles =
    variant === "outline"
      ? "border border-gray-600 bg-transparent"
      : "bg-orange-600 text-white";

  return (
    <button className={`${base} ${styles} ${className}`} {...props}>
      {children}
    </button>
  );
}
