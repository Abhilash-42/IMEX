import React from "react";

export function Alert({
  children,
  className = "",
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`rounded-lg border p-4 ${className}`}>
      {children}
    </div>
  );
}

export function AlertTitle({
  children,
  className = "",
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h4 className={`font-semibold ${className}`}>{children}</h4>;
}

export function AlertDescription({
  children,
  className = "",
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={`text-sm ${className}`}>{children}</p>;
}
