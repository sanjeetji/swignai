import type { Config } from "tailwindcss";
import { swingaiPreset } from "@swingai/ui/src/tailwind-preset";

const config: Config = {
  presets: [swingaiPreset as Config],
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
};
export default config;
