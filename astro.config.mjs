import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  base: "/neuronal-lens/",
  vite: {
    server: {
      watch: {
        ignored: /public/,
      },
    },
  },
});
