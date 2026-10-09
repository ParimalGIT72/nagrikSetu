import { useState } from "react";
import { FilePlus2, LogOut, Menu, Rows3, X } from "lucide-react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../useAuth";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  const pageTitle = location.pathname.includes("/new")
    ? "New complaint"
    : location.pathname.split("/").filter(Boolean).length > 2
      ? "Complaint details"
      : "My complaints";

  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link className="brand" to="/app/complaints" onClick={() => setMenuOpen(false)}>
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <span className="brand-name">Nagrik<span>Setu</span></span>
        </Link>
        <div className="side-caption">CITIZEN DESK</div>
        <nav className="side-nav" aria-label="Main navigation">
          <NavLink to="/app/complaints" end className={({ isActive }) => `side-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
            <Rows3 size={18} strokeWidth={1.8} /> <span>My complaints</span>
          </NavLink>
          <NavLink to="/app/complaints/new" className={({ isActive }) => `side-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
            <FilePlus2 size={18} strokeWidth={1.8} /> <span>Submit a complaint</span>
          </NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="account-mini">
            <span className="avatar" aria-hidden="true">{user?.email.slice(0, 1).toUpperCase()}</span>
            <span className="account-copy"><strong>{user?.email}</strong><small>{user?.role}</small></span>
          </div>
          <button className="side-logout" onClick={handleLogout}>
            <LogOut size={17} /> <span>Sign out</span>
          </button>
        </div>
      </aside>

      {menuOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}

      <main className="main-shell">
        <header className="topbar">
          <button className="icon-button menu-toggle" aria-label={menuOpen ? "Close menu" : "Open menu"} onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="breadcrumb"><span>Citizen desk</span><span className="crumb-slash">/</span><strong>{pageTitle}</strong></div>
          <div className="topbar-right"><span className="secure-label"><span /> Signed in</span></div>
        </header>
        <div className="page-content"><Outlet /></div>
        <footer className="app-footer"><span>Nagrik Setu</span><span>Citizen services · Maharashtra</span></footer>
      </main>
    </div>
  );
}