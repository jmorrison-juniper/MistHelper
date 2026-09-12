import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { TimezonePreference } from '@/api/client';

export interface PollingConfig {
  activeIntervalMs: number;
  passiveIntervalMs: number;
}

interface SettingsState {
  polling: PollingConfig;
  timezone: TimezonePreference;
}

interface SettingsActions {
  setPolling: (config: Partial<PollingConfig>) => void;
  setTimezone: (mode: TimezonePreference['mode']) => void;
}

const ACTIVE_DEFAULT = Number(import.meta.env.VITE_POLLING_ACTIVE_MS) || 5000;
const PASSIVE_DEFAULT = Number(import.meta.env.VITE_POLLING_PASSIVE_MS) || 30000;

export const useSettings = create<SettingsState & SettingsActions>()(
  persist(
    (set) => ({
      polling: {
        activeIntervalMs: ACTIVE_DEFAULT,
        passiveIntervalMs: PASSIVE_DEFAULT,
      },
      timezone: { mode: 'local' },

      setPolling: (config) =>
        set((state) => ({
          polling: { ...state.polling, ...config },
        })),

      setTimezone: (mode) => set({ timezone: { mode } }),
    }),
    { name: 'ops-portal-settings' },
  ),
);
