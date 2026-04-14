import { useState, useEffect, useCallback } from "react";
import { getAuthSession, login, logout, getUsage } from "../chrome-api";

export interface AuthState {
  loggedIn: boolean;
  loading: boolean;
  loggingIn: boolean;
  usage: { used: number; limit: number; plan: string } | null;
}

const INITIAL: AuthState = { loggedIn: false, loading: true, loggingIn: false, usage: null };

export function useAuth() {
  const [state, setState] = useState<AuthState>(INITIAL);

  const refresh = useCallback(async () => {
    try {
      const session = await getAuthSession();
      const loggedIn = !!session;
      setState((s) => ({ ...s, loggedIn, loading: false, loggingIn: false, usage: null }));

      if (loggedIn) {
        const usage = await getUsage().catch(() => null);
        setState((s) => ({ ...s, usage }));
      }
    } catch {
      setState((s) => ({ ...s, loggedIn: false, loading: false, loggingIn: false }));
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleLogin = useCallback(async () => {
    setState((s) => ({ ...s, loggingIn: true }));
    try {
      await login();
    } catch {
      // user closed the OAuth window
    }
    await refresh();
  }, [refresh]);

  const handleLogout = useCallback(async () => {
    await logout();
    setState({ loggedIn: false, loading: false, loggingIn: false, usage: null });
  }, []);

  return { ...state, login: handleLogin, logout: handleLogout, refreshUsage: refresh };
}
