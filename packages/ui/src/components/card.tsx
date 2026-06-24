import * as React from "react";
import { cn } from "../cn";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-border bg-card text-foreground shadow-sm", className)}
      {...props}
    />
  );
}
