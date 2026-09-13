import { create } from 'zustand';

export interface OperatorIdentity {
  email: string;
  name: string;
  role: 'msp' | 'org_admin' | 'org_viewer';
  orgs: OrgRef[];
}

export interface OrgRef {
  orgId: string;
  name: string;
}

export interface SessionState {
  isAuthenticated: boolean;
  sessionId: string | null;
  operator: OperatorIdentity | null;
  expiresAt: string | null;
  returnUrl: string | null;
}

interface SessionActions {
  login: (sessionId: string, operator: OperatorIdentity, expiresAt: string) => void;
  logout: () => void;
  setReturnUrl: (url: string | null) => void;
  isExpired: () => boolean;
}

const initialState: SessionState = {
  isAuthenticated: false,
  sessionId: null,
  operator: null,
  expiresAt: null,
  returnUrl: null,
};

export const useSession = create<SessionState & SessionActions>()((set, get) => ({
  ...initialState,

  login: (sessionId, operator, expiresAt) =>
    set({
      isAuthenticated: true,
      sessionId,
      operator,
      expiresAt,
      returnUrl: null,
    }),

  logout: () => set(initialState),

  setReturnUrl: (url) => set({ returnUrl: url }),

  isExpired: () => {
    const { expiresAt } = get();
    if (!expiresAt) return true;
    return new Date(expiresAt) <= new Date();
  },
}));
