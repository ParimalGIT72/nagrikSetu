import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ArrowLeft, ArrowUpRight, Check, FilePlus2, LocateFixed, MapPin, RefreshCw, Send } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../useAuth";
import type { Complaint, ComplaintSubmission } from "../types";

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function statusClass(status: string) {
  return status.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

function PageHeading({ kicker, title, children }: { kicker: string; title: string; children?: ReactNode }) {
  return (
    <div className="page-heading">
      <div><div className="page-kicker">{kicker}</div><h1>{title}</h1></div>
      {children}
    </div>
  );
}

export function ComplaintListPage() {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    setLoading(true);
    setError("");
    api.myComplaints(accessToken).then((result) => {
      if (!active) return;
      setItems(result.items);
      setTotal(result.total);
    }).catch((caught: unknown) => {
      if (active) setError(caught instanceof ApiError ? caught.message : "Your complaints could not be loaded.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [accessToken, refreshCount]);

  return (
    <>
      <PageHeading kicker="CITIZEN DESK / RECORDS" title="My complaints">
        <Link className="primary-button heading-action" to="/app/complaints/new"><FilePlus2 size={17} /> New complaint</Link>
      </PageHeading>
      <section className="summary-strip" aria-label="Complaint summary">
        <div className="summary-number"><strong>{loading ? "—" : total}</strong><span>All submissions</span></div>
        <div className="summary-divider" />
        <div className="summary-note"><span className="summary-dot" /> Records linked to <strong>your account</strong></div>
        <button className="icon-button refresh-button" aria-label="Refresh complaints" onClick={() => setRefreshCount((count) => count + 1)} disabled={loading}><RefreshCw size={17} /></button>
      </section>

      <section className="records-section" aria-labelledby="records-title">
        <div className="section-heading"><div><span className="section-index">01</span><h2 id="records-title">Recent submissions</h2></div><span className="section-count">{loading ? "Loading" : `${items.length} shown`}</span></div>
        {loading ? (
          <div className="loading-rows" aria-label="Loading complaints"><span /><span /><span /></div>
        ) : error ? (
          <div className="state-panel error-panel" role="alert"><p>{error}</p><button className="text-button" onClick={() => setRefreshCount((count) => count + 1)}>Try again <ArrowUpRight size={15} /></button></div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-symbol"><FilePlus2 size={23} /></div>
            <div><h3>No complaints yet</h3><p>Your submitted grievances will appear here.</p></div>
            <Link className="outline-button" to="/app/complaints/new">Start a submission <ArrowUpRight size={15} /></Link>
          </div>
        ) : (
          <div className="complaint-table" role="list">
            {items.map((complaint, index) => (
              <Link className="complaint-row" role="listitem" to={`/app/complaints/${encodeURIComponent(complaint.complaint_id)}`} key={complaint.complaint_id}>
                <span className="row-index">{String(index + 1).padStart(2, "0")}</span>
                <span className="row-main"><strong>{complaint.complaint_id}</strong><span>{complaint.text}</span></span>
                <span className={`status-badge status-${statusClass(complaint.status)}`}><i />{complaint.status}</span>
                <time className="row-date" dateTime={complaint.created_at}>{dateLabel(complaint.created_at)}</time>
                <ArrowUpRight className="row-arrow" size={17} />
              </Link>
            ))}
          </div>
        )}
      </section>
      <div className="records-footnote"><span>Showing up to 50 records</span><span>Linked to your signed-in account</span></div>
    </>
  );
}

export function NewComplaintPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [image, setImage] = useState<File | undefined>();
  const imageInput = useRef<HTMLInputElement>(null);
  const [locationState, setLocationState] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<ComplaintSubmission | null>(null);
  const [busy, setBusy] = useState(false);

  function useCurrentLocation() {
    setLocationState("");
    if (!navigator.geolocation) {
      setLocationState("Location is not available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLatitude(coords.latitude.toFixed(6));
        setLongitude(coords.longitude.toFixed(6));
        setLocationState("Coordinates captured. Check the pin before submitting.");
      },
      () => setLocationState("Location permission was unavailable. Enter coordinates manually."),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  function chooseImage(file?: File) {
    setError("");
    if (!file) {
      setImage(undefined);
      if (imageInput.current) imageInput.current.value = "";
      return;
    }
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setImage(undefined);
      if (imageInput.current) imageInput.current.value = "";
      setError("Choose a JPG, PNG or WebP image.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setImage(undefined);
      if (imageInput.current) imageInput.current.value = "";
      setError("The image must be 5 MB or smaller.");
      return;
    }
    setImage(file);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess(null);
    if (text.trim().length < 10 || text.trim().length > 2000) {
      setError("Describe the issue in 10 to 2,000 characters.");
      return;
    }
    const lat = Number(latitude);
    const lon = Number(longitude);
    if (!Number.isFinite(lat) || lat < -90 || lat > 90 || !Number.isFinite(lon) || lon < -180 || lon > 180) {
      setError("Enter a valid latitude from -90 to 90 and longitude from -180 to 180.");
      return;
    }
    if (!accessToken) return;
    setBusy(true);
    try {
      const result = await api.submitComplaint({ text: text.trim(), latitude: lat, longitude: lon, image }, accessToken);
      setSuccess(result);
      setText("");
      setImage(undefined);
      if (imageInput.current) imageInput.current.value = "";
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Your complaint could not be submitted.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeading kicker="CITIZEN DESK / NEW RECORD" title="Submit a complaint">
        <Link className="back-link" to="/app/complaints"><ArrowLeft size={16} /> All complaints</Link>
      </PageHeading>
      {success ? (
        <section className="submission-success" role="status">
          <div className="success-seal"><Check size={24} /></div>
          <div className="page-kicker">RECEIVED / {success.status}</div>
          <h2>Your complaint is on record.</h2>
          <p>{success.message}</p>
          <div className="receipt-number"><span>REFERENCE NUMBER</span><strong>{success.complaint_id}</strong></div>
          <div className="success-actions">
            <button className="primary-button" onClick={() => navigate(`/app/complaints/${encodeURIComponent(success.complaint_id)}`)}>View complaint <ArrowUpRight size={16} /></button>
            <button className="outline-button" onClick={() => setSuccess(null)}>Submit another</button>
          </div>
        </section>
      ) : (
        <div className="submission-grid">
          <form className="complaint-form" onSubmit={submit}>
            <div className="form-section-title"><span>01</span><div><h2>What happened?</h2><p>Give a clear description of the civic issue.</p></div></div>
            <label className="form-field complaint-description">
              <span>Description <small>10–2,000 characters</small></span>
              <textarea value={text} onChange={(event) => setText(event.target.value)} minLength={10} maxLength={2000} rows={7} placeholder="Describe the issue and where it is affecting the community…" required />
              <span className="character-count">{text.length} / 2,000</span>
            </label>

            <div className="form-section-title location-title"><span>02</span><div><h2>Where is it?</h2><p>Coordinates help route the report to the right area.</p></div></div>
            <div className="coordinate-grid">
              <label className="form-field"><span>Latitude</span><input className="plain-input" type="number" min="-90" max="90" step="any" value={latitude} onChange={(event) => setLatitude(event.target.value)} placeholder="18.5204" required /></label>
              <label className="form-field"><span>Longitude</span><input className="plain-input" type="number" min="-180" max="180" step="any" value={longitude} onChange={(event) => setLongitude(event.target.value)} placeholder="73.8567" required /></label>
              <button className="location-button" type="button" onClick={useCurrentLocation}><LocateFixed size={16} /> Use my location</button>
            </div>
            {locationState && <p className="inline-note" role="status">{locationState}</p>}

            <div className="form-section-title attachment-title"><span>03</span><div><h2>Supporting image <small>Optional</small></h2><p>JPG, PNG or WebP · up to 5 MB</p></div></div>
            <div className="upload-box">
              <label className="upload-control">
                <input ref={imageInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => chooseImage(event.target.files?.[0])} />
                <span className="upload-symbol"><FilePlus2 size={19} /></span>
                <span><strong>{image ? image.name : "Choose an image"}</strong><small>{image ? `${(image.size / 1024 / 1024).toFixed(2)} MB · ready to upload` : "A photo can help document the issue"}</small></span>
              </label>
              {image && <button type="button" className="remove-file" onClick={() => chooseImage(undefined)}>Remove</button>}
            </div>

            {error && <div className="form-alert" role="alert">{error}</div>}
            <div className="submit-row"><p><MapPin size={15} /> Submitted under your citizen account</p><button className="primary-button" disabled={busy}>{busy ? <span className="spinner spinner-light" /> : <>Submit complaint <Send size={16} /></>}</button></div>
          </form>
          <aside className="submission-aside">
            <div className="aside-index">RECORD / 01</div>
            <div className="aside-rule" />
            <h3>Filed by you.<br /><em>Tracked by reference.</em></h3>
            <p>Your account is linked automatically. A reference number appears once the complaint has been accepted.</p>
            <div className="aside-coordinate-mark"><span>NS</span><i /><span>2026</span></div>
          </aside>
        </div>
      )}
    </>
  );
}

export function ComplaintDetailPage() {
  const { complaintId = "" } = useParams();
  const { accessToken } = useAuth();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      if (!accessToken) return;
      setLoading(true);
      setError("");
      try {
        const result = await api.complaint(complaintId, accessToken);
        if (active) setComplaint(result);
      } catch (caught) {
        if (active) setError(caught instanceof ApiError ? caught.message : "Complaint details could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [accessToken, complaintId]);

  return (
    <>
      <PageHeading kicker="CITIZEN DESK / RECORD" title="Complaint details">
        <Link className="back-link" to="/app/complaints"><ArrowLeft size={16} /> All complaints</Link>
      </PageHeading>
      {loading ? <div className="detail-loading"><span className="spinner" /><span>Loading complaint record</span></div> : error ? (
        <div className="state-panel error-panel" role="alert"><p>{error}</p><Link className="text-button" to="/app/complaints">Return to my complaints <ArrowUpRight size={15} /></Link></div>
      ) : complaint ? (
        <article className="detail-record">
          <header className="detail-record-head"><div><span className="page-kicker">REFERENCE NUMBER</span><h2>{complaint.complaint_id}</h2></div><span className={`status-badge status-${statusClass(complaint.status)}`}><i />{complaint.status}</span></header>
          <div className="detail-meta"><div><span>SUBMITTED</span><time dateTime={complaint.created_at}>{dateLabel(complaint.created_at)}</time></div><div><span>LAST UPDATED</span><time dateTime={complaint.updated_at}>{dateLabel(complaint.updated_at)}</time></div></div>
          <section className="detail-section"><div className="page-kicker">DESCRIPTION</div><p className="detail-description">{complaint.text}</p></section>
          <section className="detail-section detail-location"><div className="page-kicker">LOCATION</div><div className="coordinate-value"><MapPin size={17} /><span>{complaint.latitude.toFixed(5)}, {complaint.longitude.toFixed(5)}</span></div></section>
          {complaint.image_path && <section className="detail-section detail-attachment"><div className="page-kicker">SUPPORTING MATERIAL</div><span className="attachment-confirmed"><Check size={15} /> Image attached</span><p>Image previews are not shown in this portal.</p></section>}
          {complaint.is_flagged && <section className="review-note"><strong>Review note</strong><span>This submission has been flagged for staff review.</span></section>}
        </article>
      ) : null}
    </>
  );
}