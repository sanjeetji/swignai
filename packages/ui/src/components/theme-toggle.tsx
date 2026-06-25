"use client";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "./button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  // theme is unknown on the server → render a stable placeholder until mounted,
  // otherwise the icon differs server↔client and React throws a hydration error.
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="sm" aria-label="Toggle theme">
        <span className="h-4 w-4" />
      </Button>
    );
  }

  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "dark" ? Moon : theme === "system" ? Monitor : Sun;
  return (
    <Button variant="ghost" size="sm" aria-label="Toggle theme" onClick={() => setTheme(next)}>
      <Icon className="h-4 w-4" />
    </Button>
  );
}
