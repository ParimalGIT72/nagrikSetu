import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider } from "./auth";
import { useAuth } from "./useAuth";
import AppLayout from "./layout/AppLayout";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { ComplaintDetailPage, ComplaintListPage, NewComplaintPage } from "./pages/ComplaintPages";

function LoadingScreen() {
  return <main className="session-loading" aria-label="Checking your session"><span className="spinner" /></main>;
}

function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <LoadingScreen />;
  if (status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

function CitizenOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "citizen") return <Navigate to="/staff-entry" replace />;
  return children;
}

function PublicOnly({ children }: { children: ReactNode }) {
  const { status, user } = useAuth();
  if (status === "loading") return <LoadingScreen />;
  if (status === "authenticated") return <Navigate to={user?.role === "citizen" ? "/app/complaints" : "/staff-entry"} replace />;
  return children;
}

function StaffEntryPage() {
  const { status, user, logout } = useAuth();
  const navigate = useNavigate();
  if (status === "loading") return <LoadingScreen />;
  if (status === "anonymous") return <Navigate to="/login" replace />;
  if (user?.role === "citizen") return <Navigate to="/app/complaints" replace />;
  return (
    <main className="staff-entry">
      <div className="staff-entry-mark"><span className="brand-mark" aria-hidden="true"><span /></span><span className="brand-name">Nagrik<span>Setu</span></span></div>
      <div className="page-kicker">STAFF ACCOUNT / {user?.role.toUpperCase()}</div>
      <h1>Staff dashboard<br /><em>not connected.</em></h1>
      <p>This frontend currently includes citizen complaint services only. Your staff account is authenticated, but no officer dashboard is available here.</p>
      <button className="primary-button" onClick={() => void logout().then(() => navigate("/login", { replace: true }))}>Sign out</button>
    </main>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app/complaints" replace />} />
      <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />
      <Route path="/staff-entry" element={<StaffEntryPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/app" element={<CitizenOnly><AppLayout /></CitizenOnly>}>
          <Route index element={<Navigate to="complaints" replace />} />
          <Route path="complaints" element={<ComplaintListPage />} />
          <Route path="complaints/new" element={<NewComplaintPage />} />
          <Route path="complaints/:complaintId" element={<ComplaintDetailPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}