import type { Complaint, ComplaintList, ComplaintSubmission, TokenResponse, User } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
export const AUTH_INVALID_EVENT = "nagrik:auth-invalid";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = payload.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) return String(item.msg);
        return "Please check the submitted information.";
      }).join(" ");
    }
  }
  return "The request could not be completed. Please try again.";
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Unable to reach Nagrik Setu. Check your connection and try again.", 0);
  }

  if (response.status === 401 && token) {
    window.dispatchEvent(new Event(AUTH_INVALID_EVENT));
  }
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = undefined;
    }
    throw new ApiError(errorMessage(payload), response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  register(email: string, password: string) {
    return request<User>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, role: "citizen" }),
    });
  },
  login(email: string, password: string) {
    return request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  me(token: string) {
    return request<User>("/api/auth/me", {}, token);
  },
  logout(token: string) {
    return request<void>("/api/auth/logout", { method: "POST" }, token);
  },
  myComplaints(token: string) {
    return request<ComplaintList>("/api/auth/me/complaints?limit=50&offset=0", {}, token);
  },
  complaint(complaintId: string, token: string) {
    return request<Complaint>(`/api/complaints/${encodeURIComponent(complaintId)}`, {}, token);
  },
  submitComplaint(input: {
    text: string;
    latitude: number;
    longitude: number;
    image?: File;
  }, token: string) {
    const body = new FormData();
    body.set("text", input.text);
    body.set("latitude", String(input.latitude));
    body.set("longitude", String(input.longitude));
    if (input.image) body.set("image", input.image);
    return request<ComplaintSubmission>("/api/complaints", { method: "POST", body }, token);
  },
};