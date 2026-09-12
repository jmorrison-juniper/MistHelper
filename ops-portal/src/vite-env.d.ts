/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_POLLING_ACTIVE_MS: string;
  readonly VITE_POLLING_PASSIVE_MS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
