import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';

// Vite 8 bundles with Rolldown, and Rolldown accepts a function for
// `manualChunks` only. The object form that this file used before is not a
// legal value, so the type check stopped the build. Issue #1958 records the
// defect. This table keeps the two original groups, `vendor` and `query`.
//
// The table also names the direct dependency of each listed package. The
// object form pulled those dependencies into the same chunk, so the table
// must name them to hold the split at the same boundary.
const CHUNK_FOR_PACKAGE: ReadonlyArray<readonly [string, string]> = [
  ['react', 'vendor'], // The original `vendor` group listed this package.
  ['react-dom', 'vendor'], // The original `vendor` group listed this package.
  ['react-router', 'vendor'], // The original `vendor` group listed this package.
  ['scheduler', 'vendor'], // react-dom depends on this package.
  ['cookie-es', 'vendor'], // react-router depends on this package.
  ['@tanstack/react-query', 'query'], // The original `query` group listed this package.
  ['@tanstack/query-core', 'query'], // @tanstack/react-query depends on this package.
];

// The path segment that starts the package part of a module identifier.
const PACKAGE_ROOT = '/node_modules/';

/**
 * Return the chunk name for one module, or undefined for the default chunk.
 *
 * @param moduleId - The absolute identifier of the module that Rolldown reads.
 * @returns The chunk name, or undefined when the module keeps the default.
 */
function chunkForPackage(moduleId: string): string | undefined {
  // Windows reports a backslash separator, so one form makes the match host independent.
  const modulePath = moduleId.replaceAll('\\', '/');
  // The last marker wins, because a nested install repeats the segment.
  const start = modulePath.lastIndexOf(PACKAGE_ROOT);
  if (start === -1) {
    // The module is application source, so it belongs in the default chunk.
    return undefined;
  }
  // Drop the prefix so the text starts at the package name.
  const packagePath = modulePath.slice(start + PACKAGE_ROOT.length);
  // The trailing slash holds the name boundary, so `react` cannot match `react-router`.
  const entry = CHUNK_FOR_PACKAGE.find(([name]) => packagePath.startsWith(`${name}/`));
  // An unlisted package keeps the default chunk, which the object form also did.
  return entry?.[1];
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': resolve(import.meta.dirname!, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        // Rolldown calls this function one time for each module in the graph.
        manualChunks: chunkForPackage,
      },
    },
  },
});
