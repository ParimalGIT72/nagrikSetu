import { useState, type FormEvent, type ReactNode } from "react";
import { ArrowRight, Eye, EyeOff, Landmark, LockKeyhole, Mail } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../useAuth";

function AuthFrame({ children, mode }: { children: ReactNode; mode: "login" | "register" }) {
  return (
    <main className="auth-page">
      <section className="auth-aside">
        <Link className="brand auth-brand" to="/login">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <span className="brand-name">Nagrik<span>Setu</span></span>
        </Link>
        <div className="auth-aside-copy">
          <div className="auth-kicker"><Landmark size={15} /> PUBLIC SERVICE PORTAL</div>
          <h1>Your city.<br /><em>On record.</em></h1>
          <p>Citizen grievance services</p>
        </div>
        <div className="aside-coordinate"><span>18°31′ N</span><i /> <span>73°51′ E</span></div>
        <div className="auth-aside-foot"><span>महाराष्ट्र शासन</span><span>Citizen access · {mode === "login" ? "01" : "02"}</span></div>
      </section>
      <section className="auth-main">
        <div className="auth-form-wrap">{children}</div>
        <div className="auth-footer"><span>Secure citizen access</span><span>English · मराठी</span></div>
      </section>
    </main>
  );
}

function PasswordInput({ label, value, onChange, autoComplete, minLength }: {
  label: string;
  value: string;
  onChange(value: string): void;
  autoComplete: string;
  minLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="form-field">
      <span>{label}</span>
      <span className="input-shell">
        <LockKeyhole size={17} aria-hidden="true" />
        <input
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete={autoComplete}
          minLength={minLength}
          maxLength={128}
          required
        />
        <button className="input-icon-button" type="button" aria-label={visible ? "Hide password" : "Show password"} onClick={() => setVisible(!visible)}>
          {visible ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </span>
    </label>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const profile = await login(email.trim(), password);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(profile.role === "citizen" ? from || "/app/complaints" : "/staff-entry", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign in could not be completed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame mode="login">
      <div className="form-eyebrow">WELCOME BACK <span>—</span> 01</div>
      <h2>Sign in</h2>
      <p className="form-intro">Enter your registered email to continue.</p>
      <form className="auth-form" onSubmit={submit}>
        <label className="form-field">
          <span>Email address</span>
          <span className="input-shell"><Mail size={17} aria-hidden="true" /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" maxLength={254} required /></span>
        </label>
        <PasswordInput label="Password" value={password} onChange={setPassword} autoComplete="current-password" />
        {error && <div className="form-alert" role="alert">{error}</div>}
        <button className="primary-button auth-submit" disabled={busy}>
          {busy ? <span className="spinner spinner-light" /> : <>Continue <ArrowRight size={17} /></>}
        </button>
      </form>
      <p className="auth-switch">New to Nagrik Setu? <Link to="/register">Create an account</Link></p>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (password !== confirmation) {
      setError("Your passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await register(email.trim(), password);
      navigate("/app/complaints", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Account creation could not be completed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthFrame mode="register">
      <div className="form-eyebrow">CITIZEN ACCESS <span>—</span> 02</div>
      <h2>Create account</h2>
      <p className="form-intro">Your account details stay with your citizen profile.</p>
      <form className="auth-form" onSubmit={submit}>
        <label className="form-field">
          <span>Email address</span>
          <span className="input-shell"><Mail size={17} aria-hidden="true" /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" maxLength={254} required /></span>
        </label>
        <PasswordInput label="Password · 12 characters minimum" value={password} onChange={setPassword} autoComplete="new-password" minLength={12} />
        <PasswordInput label="Confirm password" value={confirmation} onChange={setConfirmation} autoComplete="new-password" minLength={12} />
        {error && <div className="form-alert" role="alert">{error}</div>}
        <button className="primary-button auth-submit" disabled={busy}>
          {busy ? <span className="spinner spinner-light" /> : <>Create citizen account <ArrowRight size={17} /></>}
        </button>
      </form>
      <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>
      <p className="auth-note">Staff accounts are provisioned separately.</p>
    </AuthFrame>
  );
}