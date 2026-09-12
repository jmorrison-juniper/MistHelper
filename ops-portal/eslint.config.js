// The eslint flat configuration for the ops portal.
//
// eslint 10 reads this file only. The old `.eslintrc.cjs` format stopped
// working in eslint 9, so the lint step failed on every run. Issue #1852
// tracks that defect.
//
// This file is a real migration, not a compatibility shim. Each plugin
// supplies its own flat configuration, so no `FlatCompat` wrapper is needed.

import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import prettier from 'eslint-config-prettier';

export default [
  // Skip the build output and the vite type shim, because neither is source.
  { ignores: ['dist/**', 'node_modules/**', '*.d.ts'] },

  // The base rule set that eslint ships. The old config named this
  // 'eslint:recommended'.
  js.configs.recommended,

  // The TypeScript rule set. The flat variant carries the parser and the
  // plugin together, so no separate parser block is needed for it.
  ...tsPlugin.configs['flat/recommended'],

  // The React rule set and the automatic JSX runtime. The runtime entry turns
  // off the rule that demands a React import in every file.
  react.configs.flat.recommended,
  react.configs.flat['jsx-runtime'],

  // The rules of hooks. The `flat` entry is the one with a plugins object.
  // The `recommended-latest` entry still carries a plugins array, which
  // eslint 10 refuses to read.
  reactHooks.configs.flat.recommended,

  // The accessibility rule set for JSX.
  jsxA11y.flatConfigs.recommended,

  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
      // The old config set `env: { browser: true, es2022: true }`. Flat config
      // names the same globals through the `globals` package.
      globals: {
        ...globals.browser,
        ...globals.es2022,
      },
    },
    settings: {
      // Name the React version rather than detecting it. eslint-plugin-react
      // 7.37.5 detects the version through an eslint 9 context API that
      // eslint 10 removed, so 'detect' throws. Issue #1852 records this.
      react: { version: '19.2' },
    },
    rules: {
      // TypeScript checks the prop types, so the runtime check adds no value.
      'react/prop-types': 'off',
      // A leading underscore marks an argument that the code keeps on purpose.
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      // Judge the href only. The other aspects of this rule fight the router.
      'jsx-a11y/anchor-is-valid': ['error', { aspects: ['invalidHref'] }],
    },
  },

  {
    // A test file runs under vitest, so it needs the node globals as well.
    files: ['**/*.{test,spec}.{ts,tsx}'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },

  // Turn off every rule that argues with prettier. This entry must stay last.
  prettier,
];
