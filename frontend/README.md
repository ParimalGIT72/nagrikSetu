# Nagrik Setu Citizen Desk

React, TypeScript and Vite frontend for the existing FastAPI service.

## Configuration

Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` to the backend origin. This is a public URL setting; never put backend credentials or signing keys in `VITE_*` variables. The backend must allow the frontend origin through `FRONTEND_ORIGINS`.

## Session policy

The API returns a short-lived bearer access token with `expires_in`. The frontend stores that token only in `sessionStorage` for the current tab, checks the actual expiry, and validates restored sessions with `GET /api/auth/me`. It clears the token on expiry, an authenticated 401, or logout. There is no refresh endpoint and no `localStorage` persistence. `sessionStorage` is still readable by same-origin JavaScript, so this does not protect against XSS; use a strict content-security policy and avoid unsafe HTML. Logout attempts backend revocation and clears the local session even if the API is unreachable.

## Commands

```powershell
npm install
npm run dev
npm run lint
npm test
npm run build
```

Citizen registration uses email and password only; the backend has no name field. Staff registration is not offered. Complaint submission sends multipart `text`, `latitude`, `longitude`, and optional `image`, without a client-supplied `user_id`.

The API currently serves uploaded files publicly under `/uploads`. This frontend does not render `image_path` as a URL or fetch image previews, but the files themselves are not private.