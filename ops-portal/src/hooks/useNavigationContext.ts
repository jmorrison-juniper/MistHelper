import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface NavigationContext {
  mspId: string | null;
  orgId: string | null;
  orgName: string | null;
  siteId: string | null;
  siteName: string | null;
  deviceId: string | null;
}

interface NavigationActions {
  setOrg: (orgId: string, orgName: string) => void;
  setSite: (siteId: string, siteName: string) => void;
  setDevice: (deviceId: string) => void;
  setMsp: (mspId: string) => void;
  clearOrg: () => void;
  clearSite: () => void;
  clearDevice: () => void;
  reset: () => void;
}

const initialState: NavigationContext = {
  mspId: null,
  orgId: null,
  orgName: null,
  siteId: null,
  siteName: null,
  deviceId: null,
};

export const useNavigationContext = create<NavigationContext & NavigationActions>()(
  persist(
    (set) => ({
      ...initialState,

      setOrg: (orgId, orgName) =>
        set({ orgId, orgName, siteId: null, siteName: null, deviceId: null }),

      setSite: (siteId, siteName) =>
        set((state) => {
          if (!state.orgId) return state;
          return { ...state, siteId, siteName, deviceId: null };
        }),

      setDevice: (deviceId) =>
        set((state) => {
          if (!state.siteId) return state;
          return { ...state, deviceId };
        }),

      setMsp: (mspId) => set({ ...initialState, mspId }),

      clearOrg: () => set({ orgId: null, orgName: null, siteId: null, siteName: null, deviceId: null }),

      clearSite: () => set({ siteId: null, siteName: null, deviceId: null }),

      clearDevice: () => set({ deviceId: null }),

      reset: () => set(initialState),
    }),
    { name: 'ops-portal-nav' },
  ),
);
