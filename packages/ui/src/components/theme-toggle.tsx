"use client";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "./button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "dark" ? Moon : theme === "system" ? Monitor : Sun;
  return (
    <Button variant="ghost" size="sm" aria-label="Toggle theme" onClick={() => setTheme(next)}>
      <Icon className="h-4 w-4" />
    </Button>
  );
}
