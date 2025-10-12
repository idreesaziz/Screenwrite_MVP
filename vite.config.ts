import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  resolve: {
    alias: {
      "~": "/home/idrees-mustafa/Dev/screenwrite/app",
      "remotion-animated": "/node_modules/remotion-animated-root/packages/remotion-animated/dist/index.js"
    }
  }
});
