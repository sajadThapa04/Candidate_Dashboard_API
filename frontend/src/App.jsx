import { useEffect, useMemo, useState } from "react";
import {
  Brain,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  LogOut,
  MessageSquarePlus,
  RefreshCcw,
  Save,
  Search,
  Shield,
  Star,
  UserRound,
} from "lucide-react";
import { api, ApiError, API_BASE_URL } from "./api/client";

const pageSize = 20;
const statusOptions = ["", "new", "reviewed", "hired", "rejected"];
const roleOptions = [
  "",
  "Full Stack Engineer",
  "Backend Engineer",
  "Frontend Engineer",
  "DevOps Engineer",
  "Data Engineer",
  "QA Automation Engineer",
];
const skillOptions = ["", "Python", "FastAPI", "React", "TypeScript", "Docker", "AWS", "Playwright"];
const scoreCategories = ["Technical", "Communication", "Problem Solving", "Ownership", "Culture Fit"];

function decodeJwt(token) {
  try {
    return JSON.parse(window.atob(token.split(".")[1]));
  } catch {
    return {};
  }
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("tk_token") || "");
  const [loginForm, setLoginForm] = useState({ email: "admin@techkraft.dev", password: "Password123!" });
  const [authError, setAuthError] = useState("");
  const [filters, setFilters] = useState({ status: "", role_applied: "", skill: "", keyword: "", offset: 0, limit: pageSize });
  const [candidatePage, setCandidatePage] = useState({ items: [], total: 0, offset: 0, limit: pageSize });
  const [selectedId, setSelectedId] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [scoreForm, setScoreForm] = useState({ category: "Technical", score: 3, note: "" });
  const [notesDraft, setNotesDraft] = useState("");
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [savingScore, setSavingScore] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [notice, setNotice] = useState("");

  const user = useMemo(() => decodeJwt(token), [token]);
  const isAdmin = user.role === "admin";

  useEffect(() => {
    if (!token) {
      return;
    }
    loadCandidates(filters);
  }, [token, filters.status, filters.role_applied, filters.skill, filters.keyword, filters.offset]);

  useEffect(() => {
    if (!token || !selectedId) {
      return;
    }
    loadCandidate(selectedId);
  }, [token, selectedId]);

  async function loadCandidates(nextFilters = filters) {
    setLoadingList(true);
    setNotice("");
    try {
      const page = await api.listCandidates(token, nextFilters);
      setCandidatePage(page);
      if (!selectedId && page.items.length > 0) {
        setSelectedId(page.items[0].id);
      }
      if (selectedId && !page.items.some((candidate) => candidate.id === selectedId) && page.items.length > 0) {
        setSelectedId(page.items[0].id);
      }
    } catch (error) {
      setNotice(error.message);
    } finally {
      setLoadingList(false);
    }
  }

  async function loadCandidate(id) {
    setLoadingDetail(true);
    setNotice("");
    try {
      const candidate = await api.getCandidate(token, id);
      setSelectedCandidate(candidate);
      setNotesDraft(candidate.internal_notes || "");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setAuthError("");
    try {
      const response = await api.login(loginForm);
      localStorage.setItem("tk_token", response.access_token);
      setToken(response.access_token);
    } catch (error) {
      setAuthError(error instanceof ApiError ? error.message : "Could not sign in");
    }
  }

  function handleLogout() {
    localStorage.removeItem("tk_token");
    setToken("");
    setSelectedCandidate(null);
    setSelectedId("");
  }

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value, offset: 0 }));
  }

  async function submitScore(event) {
    event.preventDefault();
    if (!selectedCandidate) {
      return;
    }
    setSavingScore(true);
    setNotice("");
    try {
      await api.submitScore(token, selectedCandidate.id, {
        category: scoreForm.category,
        score: Number(scoreForm.score),
        note: scoreForm.note || null,
      });
      setScoreForm({ category: "Technical", score: 3, note: "" });
      await loadCandidate(selectedCandidate.id);
      setNotice("Score submitted.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setSavingScore(false);
    }
  }

  async function generateSummary() {
    if (!selectedCandidate) {
      return;
    }
    setSummaryLoading(true);
    setNotice("");
    try {
      await api.generateSummary(token, selectedCandidate.id);
      await loadCandidate(selectedCandidate.id);
      setNotice("AI summary generated.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function saveInternalNotes() {
    if (!selectedCandidate) {
      return;
    }
    setSavingNotes(true);
    setNotice("");
    try {
      const updated = await api.updateCandidate(token, selectedCandidate.id, { internal_notes: notesDraft });
      setSelectedCandidate(updated);
      setNotice("Internal notes saved.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setSavingNotes(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(candidatePage.total / pageSize));
  const currentPage = Math.floor(filters.offset / pageSize) + 1;

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div className="brand-mark">
            <Shield size={24} />
          </div>
          <h1>TechKraft Review</h1>
          <p>Sign in to score candidates and manage assessment reviews.</p>
          <form className="auth-form" onSubmit={handleLogin}>
            <label>
              Email
              <input
                type="text"
                inputMode="email"
                value={loginForm.email}
                onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
              />
            </label>
            {authError && <p className="error-text">{authError}</p>}
            <button className="primary-button" type="submit">Sign in</button>
          </form>
          <div className="demo-logins">
            <span>Admin: admin@techkraft.dev</span>
            <span>Reviewer: reviewer@techkraft.dev</span>
            <span>Password: Password123!</span>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">Candidate assessments</p>
          <h1>Review Dashboard</h1>
        </div>
        <div className="topbar-actions">
          <span className="api-pill">{API_BASE_URL}</span>
          <span className="role-pill">{isAdmin ? "Admin" : "Reviewer"}</span>
          <button className="icon-button" type="button" onClick={() => loadCandidates(filters)} aria-label="Refresh candidates">
            <RefreshCcw size={18} />
          </button>
          <button className="text-button" type="button" onClick={handleLogout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </header>

      {notice && <div className="notice">{notice}</div>}

      <section className="workspace">
        <aside className="candidate-list">
          <div className="filter-bar">
            <label className="search-field">
              <Search size={17} />
              <input
                placeholder="Search name, email, role"
                value={filters.keyword}
                onChange={(event) => updateFilter("keyword", event.target.value)}
              />
            </label>
            <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
              {statusOptions.map((status) => (
                <option key={status} value={status}>{status || "All statuses"}</option>
              ))}
            </select>
            <select value={filters.role_applied} onChange={(event) => updateFilter("role_applied", event.target.value)}>
              {roleOptions.map((role) => (
                <option key={role} value={role}>{role || "All roles"}</option>
              ))}
            </select>
            <select value={filters.skill} onChange={(event) => updateFilter("skill", event.target.value)}>
              {skillOptions.map((skill) => (
                <option key={skill} value={skill}>{skill || "All skills"}</option>
              ))}
            </select>
          </div>

          <div className="list-header">
            <span>{loadingList ? "Loading..." : `${candidatePage.total} candidates`}</span>
            <span>Page {currentPage} of {totalPages}</span>
          </div>

          <div className="candidate-scroll">
            {candidatePage.items.map((candidate) => (
              <button
                className={`candidate-row ${candidate.id === selectedId ? "active" : ""}`}
                key={candidate.id}
                type="button"
                onClick={() => setSelectedId(candidate.id)}
              >
                <span className="row-avatar"><UserRound size={18} /></span>
                <span className="row-main">
                  <strong>{candidate.name}</strong>
                  <small>{candidate.role_applied}</small>
                </span>
                <span className={`status status-${candidate.status}`}>{candidate.status}</span>
              </button>
            ))}
          </div>

          <div className="pagination">
            <button
              className="icon-button"
              type="button"
              disabled={filters.offset === 0}
              onClick={() => setFilters((current) => ({ ...current, offset: Math.max(0, current.offset - pageSize) }))}
              aria-label="Previous page"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              className="icon-button"
              type="button"
              disabled={filters.offset + pageSize >= candidatePage.total}
              onClick={() => setFilters((current) => ({ ...current, offset: current.offset + pageSize }))}
              aria-label="Next page"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </aside>

        <section className="detail-pane">
          {loadingDetail && <div className="empty-state">Loading candidate...</div>}
          {!loadingDetail && selectedCandidate && (
            <>
              <section className="profile-section">
                <div>
                  <p className="eyebrow">{selectedCandidate.status}</p>
                  <h2>{selectedCandidate.name}</h2>
                  <p>{selectedCandidate.email}</p>
                </div>
                <div className="profile-meta">
                  <span>{selectedCandidate.role_applied}</span>
                  <span>{selectedCandidate.skills.join(", ")}</span>
                </div>
              </section>

              <div className="detail-grid">
                <section className="panel">
                  <div className="panel-heading">
                    <h3><Star size={18} /> Scores</h3>
                    <span>{selectedCandidate.scores.length}</span>
                  </div>
                  <div className="score-list">
                    {selectedCandidate.scores.length === 0 && <p className="muted">No scores submitted yet.</p>}
                    {selectedCandidate.scores.map((score) => (
                      <article className="score-item" key={score.id}>
                        <div>
                          <strong>{score.category}</strong>
                          <p>{score.note || "No note provided."}</p>
                        </div>
                        <span>{score.score}/5</span>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-heading">
                    <h3><MessageSquarePlus size={18} /> Add Score</h3>
                  </div>
                  <form className="score-form" onSubmit={submitScore}>
                    <label>
                      Category
                      <select value={scoreForm.category} onChange={(event) => setScoreForm({ ...scoreForm, category: event.target.value })}>
                        {scoreCategories.map((category) => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Score
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={scoreForm.score}
                        onChange={(event) => setScoreForm({ ...scoreForm, score: event.target.value })}
                      />
                    </label>
                    <label>
                      Note
                      <textarea
                        rows="4"
                        value={scoreForm.note}
                        onChange={(event) => setScoreForm({ ...scoreForm, note: event.target.value })}
                      />
                    </label>
                    <button className="primary-button" type="submit" disabled={savingScore}>
                      {savingScore ? "Saving..." : "Submit score"}
                    </button>
                  </form>
                </section>

                <section className="panel">
                  <div className="panel-heading">
                    <h3><Brain size={18} /> AI Summary</h3>
                    <button className="text-button compact" type="button" onClick={generateSummary} disabled={summaryLoading}>
                      {summaryLoading ? "Generating..." : "Generate"}
                    </button>
                  </div>
                  <p className={selectedCandidate.ai_summary ? "" : "muted"}>
                    {summaryLoading
                      ? "Generating summary from candidate profile and reviewer scores..."
                      : selectedCandidate.ai_summary || "No summary generated yet."}
                  </p>
                </section>

                {isAdmin && (
                  <section className="panel">
                    <div className="panel-heading">
                      <h3><ClipboardList size={18} /> Internal Notes</h3>
                    </div>
                    <textarea
                      className="notes-area"
                      rows="7"
                      value={notesDraft}
                      onChange={(event) => setNotesDraft(event.target.value)}
                    />
                    <button className="primary-button" type="button" onClick={saveInternalNotes} disabled={savingNotes}>
                      <Save size={17} />
                      {savingNotes ? "Saving..." : "Save notes"}
                    </button>
                  </section>
                )}
              </div>
            </>
          )}
          {!loadingDetail && !selectedCandidate && <div className="empty-state">Select a candidate to review.</div>}
        </section>
      </section>
    </main>
  );
}

export default App;
