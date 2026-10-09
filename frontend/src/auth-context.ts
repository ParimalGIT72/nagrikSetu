import { createContext } from "react";
import type { User } from "./types";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

export interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  accessToken: string | null;
  login(email: string, password: string): Promise<User>;
  register(email: string, password: string): Promise<User>;
  logout(): Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);