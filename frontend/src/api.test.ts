import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("backend API contract", () => {
  it("registers only an email, password and citizen role", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      id: 4,
      email: "citizen@example.test",
      role: "citizen",
      is_active: true,
      created_at: "2026-10-09T12:00:00Z",
    }, 201));
    vi.stubGlobal("fetch", fetchMock);

    await api.register("citizen@example.test", "A-long-test-password-123!");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/api\/auth\/register$/);
    expect(JSON.parse(String(init.body))).toEqual({
      email: "citizen@example.test",
      password: "A-long-test-password-123!",
      role: "citizen",
    });
  });

  it("submits the exact multipart complaint fields with bearer auth and no user id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      complaint_id: "CMP-20261009-A1B2C3",
      status: "SUBMITTED",
      message: "Complaint successfully registered.",
    }, 201));
    vi.stubGlobal("fetch", fetchMock);
    const photo = new File(["image"], "road.png", { type: "image/png" });

    await api.submitComplaint({
      text: "Pothole on the road near the bus stop.",
      latitude: 18.52,
      longitude: 73.85,
      image: photo,
    }, "access-token");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const form = init.body as FormData;
    expect(url).toMatch(/\/api\/complaints$/);
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer access-token");
    expect(form.get("text")).toBe("Pothole on the road near the bus stop.");
    expect(form.get("latitude")).toBe("18.52");
    expect(form.get("longitude")).toBe("73.85");
    expect(form.get("image")).toBe(photo);
    expect(form.has("user_id")).toBe(false);
  });

  it("uses the actual authenticated complaint-history path", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ total: 0, items: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await api.myComplaints("access-token");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/auth/me/complaints");
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get("Authorization")).toBe("Bearer access-token");
  });
});