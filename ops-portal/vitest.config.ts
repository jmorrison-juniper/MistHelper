// The vitest configuration for the ops portal.
//
// Issue #1852 records that the project shipped no test file, so `vitest run`
// exited non-zero and the CI test step could not block a merge.
//
// The config reuses the vite config, so a test resolves the `@` alias exactly
// as the application does. A component test needs a DOM, so the environment is
// jsdom rather than the default node environment.

import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.ts';

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // A React component test needs a document, which node does not supply.
      environment: 'jsdom',
      // Each test imports describe, it, and expect by name. An explicit import
      // keeps the type surface clear and needs no global type declaration.
      globals: false,
      // Read a test from the source tree only, so the build output is skipped.
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      // Free the DOM between tests, so one test cannot see another one's nodes.
      restoreMocks: true,
    },
  }),
);
