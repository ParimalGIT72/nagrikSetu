import { useEffect, useState, type ReactNode } from "react";
import { AUTH_INVALID_EVENT, api } from "./api";
import { AuthContext } from "./auth-context";
import type { AuthStatus } from "./auth-context";
import type { User } from "./types";

const SESSION_KEY = "nagrik-setu.access-session";

interface StoredSession {
  accessToken: string;
  expiresAt: number;
}

function readSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as StoredSession;
    if (!session.accessToken || session.expiresAt <= Date.now()) {
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    return session;
  } catch {
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function storeSession(accessToken: string, expiresIn: number) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    accessToken,
    expiresAt: Date.now() + expiresIn * 1000,
  } satisfies StoredSession));
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    const stored = readSession();
    if (!stored) {
      setStatus("anonymous");
      return;
    }
    setAccessToken(stored.accessToken);
    api.me(stored.accessToken).then((profile) => {
      setUser(profile);
      setStatus("authenticated");
    }).catch(() => {
      clearSession();
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
    });
  }, []);

  useEffect(() => {
    const expireSession = () => {
      clearSession();
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
    };
    window.addEventListener(AUTH_INVALID_EVENT, expireSession);
    return () => window.removeEventListener(AUTH_INVALID_EVENT, expireSession);
  }, []);

  useEffect(() => {
    if (!accessToken) return;
    const stored = readSession();
    if (!stored || stored.accessToken !== accessToken) return;
    const timeout = window.setTimeout(() => {
      clearSession();
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
    }, Math.max(0, stored.expiresAt - Date.now()));
    return () => window.clearTimeout(timeout);
  }, [accessToken]);

  async function login(email: string, password: string): Promise<User> {
    const result = await api.login(email, password);
    storeSession(result.access_token, result.expires_in);
    setAccessToken(result.access_token);
    try {
      const profile = await api.me(result.access_token);
      setUser(profile);
      setStatus("authenticated");
      return profile;
    } catch (error) {
      clearSession();
      setAccessToken(null);
      throw error;
    }
  }

  async function register(email: string, password: string): Promise<User> {
    await api.register(email, password);
    return login(email, password);
  }

  async function logout() {
    const token = accessToken;
    try {
      if (token) {
        await api.logout(token);
      }
    } catch {
      // Local logout remains effective if the API is unreachable.
    } finally {
      clearSession();
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
    }
  }

  return (
    <AuthContext.Provider value={{ status, user, accessToken, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}