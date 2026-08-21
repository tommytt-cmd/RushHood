import { defineConfig } from "vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tsconfigPaths from "vite-tsconfig-paths";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    tsconfigPaths(),
    tailwindcss(),
    tanstackStart(),
  ],
  // Instructs Nitro to natively target Vercel Serverless/Edge boundaries
  nitro: {
    preset: "vercel-edge"
  }
});
