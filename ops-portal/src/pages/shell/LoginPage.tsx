import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { apiClient } from '@/api/client';
import { useSession } from '@/hooks/useSession';
import type { OperatorIdentity } from '@/hooks/useSession';

type AuthMethod = 'token' | 'credentials' | 'sso';

interface LoginResponse {
  sessionId: string;
  operator: OperatorIdentity;
  expiresAt: string;
}

function TokenForm({ onSubmit, isLoading }: { onSubmit: (token: string) => void; isLoading: boolean }) {
  const [token, setToken] = useState('');

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(token); }}
      className="space-y-4"
    >
      <div>
        <label htmlFor="api-token" className="block text-sm font-medium text-text-primary mb-1">
          API Token
        </label>
        <input
          id="api-token"
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Enter your Mist API token"
          style={{ minHeight: '40px' }}
          className="w-full border border-border-strong rounded-lg px-3 py-2 text-sm bg-surface-secondary focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors placeholder:text-text-muted"
          required
          autoComplete="off"
        />
      </div>
      <button
        type="submit"
        disabled={isLoading}
        style={{ minHeight: '42px' }}
        className="w-full py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 active:bg-brand-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
      >
        {isLoading ? 'Signing in...' : 'Sign In with Token'}
      </button>
    </form>
  );
}

const INPUT_CLASS = 'w-full border border-border-strong rounded-lg px-3 py-2 text-sm bg-surface-secondary focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors placeholder:text-text-muted';
const INPUT_STYLE = { minHeight: '40px' };
const SUBMIT_CLASS = 'w-full py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 active:bg-brand-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm';
const SUBMIT_STYLE = { minHeight: '42px' };

function CredentialsForm({ onSubmit, isLoading }: { onSubmit: (email: string, password: string, twoFa: string) => void; isLoading: boolean }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFa, setTwoFa] = useState('');

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(email, password, twoFa); }}
      className="space-y-4"
    >
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-1">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="engineer@company.com"
          style={INPUT_STYLE}
          className={INPUT_CLASS}
          required
          autoComplete="email"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-1">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={INPUT_STYLE}
          className={INPUT_CLASS}
          required
          autoComplete="current-password"
        />
      </div>
      <div>
        <label htmlFor="two-fa" className="block text-sm font-medium text-text-primary mb-1">2FA Code (optional)</label>
        <input
          id="two-fa"
          type="text"
          value={twoFa}
          onChange={(e) => setTwoFa(e.target.value)}
          placeholder="6-digit code"
          style={INPUT_STYLE}
          className={INPUT_CLASS}
          autoComplete="one-time-code"
          inputMode="numeric"
          maxLength={6}
        />
      </div>
      <button type="submit" disabled={isLoading} style={SUBMIT_STYLE} className={SUBMIT_CLASS}>
        {isLoading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  );
}

export default function LoginPage() {
  const [method, setMethod] = useState<AuthMethod>('credentials');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useSession();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const returnUrl = searchParams.get('returnUrl') ?? '/dashboard';

  async function handleLogin(body: Record<string, string>) {
    setError(null);
    setIsLoading(true);
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', body);
      const { sessionId, operator, expiresAt } = response.data;
      login(sessionId, operator, expiresAt);
      navigate(returnUrl, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  function handleTokenSubmit(token: string) {
    handleLogin({ method: 'token', token });
  }

  function handleCredentialsSubmit(email: string, password: string, twoFaCode: string) {
    handleLogin({ method: 'credentials', email, password, ...(twoFaCode ? { two_fa_code: twoFaCode } : {}) });
  }

  function handleSsoRedirect() {
    window.location.href = '/api/v1/auth/sso';
  }

  const methodTabs: { key: AuthMethod; label: string }[] = [
    { key: 'credentials', label: 'Email' },
    { key: 'token', label: 'API Token' },
    { key: 'sso', label: 'SSO' },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary px-4 py-8">
      <div className="w-full" style={{ maxWidth: '460px', minWidth: '280px' }}>
        <div className="text-center mb-6">
          <div className="inline-flex mb-3 w-14 h-14 rounded-2xl bg-brand-600 items-center justify-center shadow-md">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25A2.25 2.25 0 0 1 5.25 3h13.5A2.25 2.25 0 0 1 21 5.25Z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary">Ops Portal</h1>
          <p className="text-sm text-text-secondary mt-1">Sign in to manage your network</p>
        </div>

        <div className="bg-surface-primary rounded-xl shadow-xl border border-border-default p-5">
          <div className="flex gap-1 bg-surface-tertiary rounded-lg p-1 mb-5">
            {methodTabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => { setMethod(tab.key); setError(null); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                  method === tab.key
                    ? 'bg-white text-brand-700 shadow-sm'
                    : 'text-text-muted hover:text-text-secondary'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-4 px-3 py-2 bg-red-50 border border-red-100 rounded-lg text-sm text-status-error" role="alert">
              {error}
            </div>
          )}

          {method === 'token' && <TokenForm onSubmit={handleTokenSubmit} isLoading={isLoading} />}
          {method === 'credentials' && <CredentialsForm onSubmit={handleCredentialsSubmit} isLoading={isLoading} />}
          {method === 'sso' && (
            <div className="text-center py-3">
              <p className="text-sm text-text-secondary mb-4">
                You will be redirected to your identity provider.
              </p>
              <button
                type="button"
                onClick={handleSsoRedirect}
                className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 active:bg-brand-800 transition-colors shadow-sm"
              >
                Continue with SSO
              </button>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-text-muted mt-4">Juniper Mist Operations Platform</p>
      </div>
    </div>
  );
}
