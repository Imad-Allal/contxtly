import { useState, useEffect, useCallback } from "react";
import { getAuthSession, login, logout, getUsage } from "../chrome-api";

export interface AuthState {
  loggedIn: boolean;
  loading: boolean;
  usage: { used: number; limit: number; plan: string } | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({ loggedIn: false, loading: true, usage: null });

  const refresh = useCallback(async () => {
    try {
      const session = await getAuthSession();
      const loggedIn = !!session;

      // Unblock UI immediately — usage loads in background
      setState({ loggedIn, loading: false, usage: null });

      if (loggedIn) {
        const usage = await getUsage().catch(() => null);
        setState((s) => ({ ...s, usage }));
      }
    } catch {
      setState({ loggedIn: false, loading: false, usage: null });
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleLogin = useCallback(async () => {
    setState((s) => ({ ...s, loading: true }));
    try {
      await login();
    } catch {
      // login() will throw if user closes the OAuth window — just stop loading
    }
    await refresh();
  }, [refresh]);

  const handleLogout = useCallback(async () => {
    await logout();
    setState({ loggedIn: false, loading: false, usage: null });
  }, []);

  return { ...state, login: handleLogin, logout: handleLogout, refreshUsage: refresh };
}
