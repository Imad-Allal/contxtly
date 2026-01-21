import { defineConfig } from "vite";
import { resolve } from "path";
import { copyFileSync, mkdirSync, existsSync } from "fs";

function copyStaticFiles() {
  return {
    name: "copy-static-files",
    closeBundle() {
      const dist = resolve(__dirname, "dist");

      // Copy manifest
      copyFileSync(
        resolve(__dirname, "manifest.json"),
        resolve(dist, "manifest.json")
      );

      // Copy CSS
      if (!existsSync(resolve(dist, "styles"))) {
        mkdirSync(resolve(dist, "styles"));
      }
      copyFileSync(
        resolve(__dirname, "styles/content.css"),
        resolve(dist, "styles/content.css")
      );

      // Copy popup HTML and CSS
      if (!existsSync(resolve(dist, "popup"))) {
        mkdirSync(resolve(dist, "popup"));
      }
      copyFileSync(
        resolve(__dirname, "src/popup/popup.html"),
        resolve(dist, "popup/popup.html")
      );
      copyFileSync(
        resolve(__dirname, "src/popup/popup.css"),
        resolve(dist, "popup/popup.css")
      );
    },
  };
}

export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        content: resolve(__dirname, "src/content/content.js"),
        background: resolve(__dirname, "src/background.js"),
        popup: resolve(__dirname, "src/popup/popup.js"),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === "popup") return "popup/popup.js";
          if (chunkInfo.name === "content") return "content/content.js";
          return "[name].js";
        },
      },
    },
  },
  plugins: [copyStaticFiles()],
});
