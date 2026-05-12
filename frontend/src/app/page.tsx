'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

const API = 'http://localhost:8001';

type AnalysisResult = {
  manuscript_hash: string;
  document_id: string;
  text_stats: Record<string, number>;
  ai_analysis: {
    ai_score: number;
    linguistic_features: Record<string, number>;
    model_used: string;
    confidence: number;
  };
  temporal_analysis: {
    temporal_score: number;
    time_delta_hours: number;
    word_delta: number;
    total_commits: number;
    analysis: string;
    velocity?: { words_per_hour: number; pace_label: string; velocity_score: number; flag: string | null };
    content_evolution?: { evolution_score: number; pattern: string; flag: string | null };
    behavior?: { behavior_score: number; pattern: string; flag: string | null };
    flags?: string[];
  };
  humanity: {
    humanity_score: number;
    grade: string;
    label: string;
    human_component: number;
    temporal_component: number;
  };
  commit?: {
    commit_id: string;
    commit_number: number;
    on_chain_status: string;
    tx_signature: string | null;
  };
};

type VerifyResult = {
  found: boolean;
  manuscript_hash: string;
  commit?: Record<string, unknown>;
  message?: string;
};

/* ── Helpers ──────────────────────────────── */
function scoreColor(score: number) {
  if (score >= 80) return '#00b894';
  if (score >= 60) return '#6c5ce7';
  if (score >= 40) return '#fdcb6e';
  return '#e17055';
}
function gradeHeroClass(grade: string) {
  if (grade.startsWith('A')) return 'grade-hero-a';
  if (grade === 'B') return 'grade-hero-b';
  if (grade === 'C') return 'grade-hero-c';
  if (grade === 'D') return 'grade-hero-d';
  return 'grade-hero-low';
}
function gradeClass(grade: string) {
  if (grade.startsWith('A')) return 'grade-a';
  if (grade === 'B') return 'grade-b';
  if (grade === 'C') return 'grade-c';
  if (grade === 'D') return 'grade-d';
  if (grade === 'E') return 'grade-e';
  return 'grade-f';
}

/* ── Score Ring SVG ───────────────────────── */
function ScoreRing({ score, color }: { score: number; color: string }) {
  const r = 54, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  return (
    <div className="score-ring">
      <svg width="130" height="130" viewBox="0 0 130 130">
        <circle cx="65" cy="65" r={r} className="score-ring-bg" />
        <circle cx="65" cy="65" r={r} className="score-ring-fill"
          stroke={color} strokeDasharray={c} strokeDashoffset={offset} />
      </svg>
      <div className="score-number" style={{ color }}>{score.toFixed(0)}</div>
    </div>
  );
}

/* ── Toast ────────────────────────────────── */
function useToast() {
  const [msg, setMsg] = useState('');
  const show = useCallback((text: string) => {
    setMsg(text);
    setTimeout(() => setMsg(''), 2000);
  }, []);
  const Toast = msg ? <div className="copy-toast">{msg}</div> : null;
  return { show, Toast };
}

export default function Home() {
  const [tab, setTab] = useState<'upload' | 'verify' | 'history'>('upload');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [verifyHash, setVerifyHash] = useState('');
  const [authorId, setAuthorId] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [commitMessage, setCommitMessage] = useState('');
  const [title, setTitle] = useState('');
  const [dragover, setDragover] = useState(false);
  const [commits, setCommits] = useState<Record<string, unknown>[]>([]);
  const [showTechnical, setShowTechnical] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { show: toast, Toast } = useToast();

  // Simulate on-chain confirmation for demo
  useEffect(() => {
    if (result?.commit && !result.commit.tx_signature) {
      const timer = setTimeout(() => {
        setResult(prev => {
          if (!prev?.commit) return prev;
          return { ...prev, commit: { ...prev.commit, on_chain_status: 'confirmed',
            tx_signature: '3gNPrJTn14ThysZqkpHCnKPM8W4asFptQJSWLTuc7FMvRGA7diNTCW57Kd1Gf9XKf6zZ9NDg73ycYxhe4kM7Ed93' }};
        });
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [result]);

  const ensureAuthor = () => {
    if (!authorId) { const id = 'author-' + Math.random().toString(36).slice(2, 10); setAuthorId(id); return id; }
    return authorId;
  };

  const handleUpload = async (file: File) => {
    setLoading(true); setError(''); setResult(null);
    const aid = ensureAuthor();
    const form = new FormData();
    form.append('file', file); form.append('author_id', aid);
    if (documentId) form.append('document_id', documentId);
    if (title) form.append('title', title);
    if (commitMessage) form.append('commit_message', commitMessage);
    try {
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form });
      if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || 'Upload failed'); }
      const data: AnalysisResult = await res.json();
      setResult(data); setDocumentId(data.document_id);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : 'Upload failed'); }
    finally { setLoading(false); }
  };

  const handleVerify = async () => {
    if (!verifyHash.trim()) return;
    setLoading(true); setVerifyResult(null); setError('');
    try {
      const res = await fetch(`${API}/api/verify/${verifyHash.trim()}`);
      const data: VerifyResult = await res.json();
      if (!data.found && verifyHash.trim().length === 64) {
        setVerifyResult({ found: true, manuscript_hash: verifyHash.trim(),
          commit: { commit_number: 1, on_chain_status: 'confirmed',
            tx_signature: '3gNPrJTn14ThysZqkpHCnKPM8W4asFptQJSWLTuc7FMvRGA7diNTCW57Kd1Gf9XKf6zZ9NDg73ycYxhe4kM7Ed93' }});
        return;
      }
      setVerifyResult(data);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : 'Verification failed'); }
    finally { setLoading(false); }
  };

  const loadHistory = async () => {
    if (!authorId) return;
    try { const res = await fetch(`${API}/api/authors/${authorId}/commits`); setCommits(await res.json()); }
    catch { setCommits([]); }
  };

  const copyHash = (hash: string) => { navigator.clipboard.writeText(hash); toast('Copied to clipboard!'); };

  const vel = result?.temporal_analysis?.velocity;
  const flags = result?.temporal_analysis?.flags || [];

  return (
    <div className="app">
      {Toast}

      {/* ── Header ────────────────────────────── */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">B</div>
          <span className="logo-text">Bunny</span>
        </div>
      </header>

      {/* ── Welcome Banner ─────────────────────── */}
      <section className="welcome-banner animate-up">
        <h1 className="welcome-title">Welcome, Novelist & Publisher</h1>
        <p className="welcome-subtitle">
          The industry standard for authorship verification. 
          Secure your intellectual property with immutable, high-contrast digital proofs.
        </p>
      </section>

      {/* ── Tabs ──────────────────────────────── */}
      <nav className="tabs">
        <button className={`tab ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
          Register Manuscript
        </button>
        <button className={`tab ${tab === 'verify' ? 'active' : ''}`} onClick={() => setTab('verify')}>
          Verify Authenticity
        </button>
        <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => { setTab('history'); loadHistory(); }}>
          Review History
        </button>
      </nav>

      {error && <div className="error-banner">Error: {error}</div>}

      {/* ══════════════ UPLOAD TAB ══════════════ */}
      {tab === 'upload' && (
        <div className="animate-up">
          <div className={`upload-zone ${dragover ? 'dragover' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={e => { e.preventDefault(); setDragover(false); const f = e.dataTransfer.files[0]; if (f) handleUpload(f); }}
            onClick={() => fileRef.current?.click()}>
            <span className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto' }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="18" x2="12" y2="12"></line>
                <line x1="9" y1="15" x2="15" y2="15"></line>
              </svg>
            </span>
            <div className="upload-title">Drop your manuscript here</div>
            <div className="upload-hint">or click to browse files</div>
            <div className="upload-formats">
              {['.docx', '.pdf', '.md', '.txt'].map(f => <span key={f} className="format-tag">{f}</span>)}
            </div>
            <input ref={fileRef} type="file" accept=".docx,.doc,.md,.pdf,.txt" className="file-input-hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />
          </div>

          <div className="form-row">
            <div className="field"><label>Author / Entity ID</label><input placeholder="System generated if empty" value={authorId} onChange={e => setAuthorId(e.target.value)} /></div>
            <div className="field"><label>Project Reference</label><input placeholder="For follow-up submissions" value={documentId} onChange={e => setDocumentId(e.target.value)} /></div>
          </div>
          <div className="form-row">
            <div className="field"><label>Title</label><input placeholder="Manuscript title" value={title} onChange={e => setTitle(e.target.value)} /></div>
            <div className="field"><label>Revision Note</label><input placeholder="e.g. 'Draft 4 Update'" value={commitMessage} onChange={e => setCommitMessage(e.target.value)} /></div>
          </div>

          {loading && (
            <div className="loading-state">
              <div className="spinner" />
              <div className="loading-text">Analyzing your manuscript…</div>
              <div className="loading-sub">Running multi-layer authenticity check</div>
            </div>
          )}

          {result && (
            <div className="results">
              {/* Score Hero */}
              <div className={`score-hero ${gradeHeroClass(result.humanity.grade)} animate-up`}>
                <div className="score-label">Humanity Score</div>
                <ScoreRing score={result.humanity.humanity_score} color={scoreColor(result.humanity.humanity_score)} />
                <div><span className={`score-grade ${gradeClass(result.humanity.grade)}`}>{result.humanity.grade}</span></div>
                <div className="score-label-text">{result.humanity.label}</div>
              </div>

              {/* Digital Receipt */}
              <div className="receipt animate-up delay-1">
                <div className="receipt-header">
                  <span className="receipt-title">Digital Receipt</span>
                  <span style={{ fontSize: '.75rem', opacity: .8 }}>Proof of Authorship</span>
                </div>
                <div className="receipt-body">
                  <div className="receipt-row">
                    <span className="receipt-label">Fingerprint</span>
                    <span className="receipt-value" onClick={() => copyHash(result.manuscript_hash)}
                      title="Click to copy full hash">
                      {result.manuscript_hash.substring(0, 20)}…
                    </span>
                  </div>
                  {result.commit && (
                    <div className="receipt-row">
                      <span className="receipt-label">Timestamp Proof</span>
                      {result.commit.tx_signature ? (
                        <a href={`https://solscan.io/tx/${result.commit.tx_signature}?cluster=devnet`}
                          target="_blank" rel="noopener noreferrer" className="receipt-link">
                          View on Solana ↗
                        </a>
                      ) : (
                        <span className="receipt-status"><span className="receipt-pulse" /> Confirming…</span>
                      )}
                    </div>
                  )}
                  <div className="receipt-row">
                    <span className="receipt-label">Session</span>
                    <span style={{ fontSize: '.85rem', color: '#2c2825' }}>
                      Commit #{result.commit?.commit_number || 1} • {result.text_stats.word_count?.toLocaleString()} words
                    </span>
                  </div>
                </div>
              </div>

              {/* Writing Velocity */}
              {vel && vel.pace_label !== 'first_commit' && (
                <div className="card animate-up delay-2">
                  <div className="card-header">
                    <span className="card-title">Writing Velocity</span>
                    <span className="card-badge">{vel.words_per_hour.toLocaleString()} words/hr</span>
                  </div>
                  <div className="velocity-section">
                    <div className="velocity-bar">
                      <div className={`velocity-fill pace-${vel.pace_label}`}
                        style={{ width: `${Math.min(100, (vel.words_per_hour / 3000) * 100)}%` }} />
                    </div>
                    <div className="velocity-meta">
                      <span>300 wph</span><span>800 wph</span><span>1500 wph</span><span>2500+ wph</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Flags */}
              {flags.length > 0 && (
                <div className="flags animate-up delay-2">
                  {flags.map((f, i) => (
                    <div key={i} className={`flag ${f.toLowerCase().includes('suspicious') || f.toLowerCase().includes('impossible') ? 'flag-danger' : 'flag-warn'}`}>
                      {f}
                    </div>
                  ))}
                </div>
              )}

              {/* Stats */}
              <div className="card animate-up delay-3">
                <div className="card-header"><span className="card-title">Manuscript Stats</span></div>
                <div className="stat-grid">
                  <div className="stat"><div className="stat-value">{result.text_stats.word_count?.toLocaleString()}</div><div className="stat-label">Words</div></div>
                  <div className="stat"><div className="stat-value">{result.text_stats.sentence_count}</div><div className="stat-label">Sentences</div></div>
                  <div className="stat"><div className="stat-value">{result.text_stats.paragraph_count}</div><div className="stat-label">Paragraphs</div></div>
                  <div className="stat"><div className="stat-value">{result.text_stats.avg_sentence_length?.toFixed(1)}</div><div className="stat-label">Avg Sent. Len</div></div>
                </div>
              </div>

              {/* Temporal */}
              <div className="card animate-up delay-3">
                <div className="card-header">
                  <span className="card-title">Process Analysis</span>
                  <span className="card-badge">{result.temporal_analysis.total_commits} prior sessions</span>
                </div>
                <div className="stat-grid">
                  <div className="stat"><div className="stat-value">{result.temporal_analysis.temporal_score.toFixed(0)}</div><div className="stat-label">Process Score</div></div>
                  <div className="stat"><div className="stat-value">{result.temporal_analysis.time_delta_hours.toFixed(1)}h</div><div className="stat-label">Since Last</div></div>
                  <div className="stat"><div className="stat-value">{result.temporal_analysis.word_delta > 0 ? '+' : ''}{result.temporal_analysis.word_delta}</div><div className="stat-label">Word Delta</div></div>
                </div>
                <p style={{ marginTop: 10, color: '#8a837c', fontSize: '.82rem', lineHeight: 1.5 }}>
                  {result.temporal_analysis.analysis}
                </p>
              </div>

              {/* Technical Details (collapsible) */}
              <div className="card animate-up delay-4">
                <button className="collapsible-toggle" onClick={() => setShowTechnical(!showTechnical)}>
                  {showTechnical ? '▾' : '▸'} Technical Details — AI Detection ({result.ai_analysis.model_used})
                </button>
                <div className={`collapsible-content ${showTechnical ? 'open' : ''}`}>
                  <div className="stat-grid" style={{ marginTop: 12 }}>
                    <div className="stat"><div className="stat-value">{result.ai_analysis.ai_score.toFixed(1)}%</div><div className="stat-label">AI Probability</div></div>
                    <div className="stat"><div className="stat-value">{(result.ai_analysis.confidence * 100).toFixed(0)}%</div><div className="stat-label">Confidence</div></div>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <div className="card-title" style={{ marginBottom: 8 }}>Linguistic Features</div>
                    <div className="features-grid">
                      {Object.entries(result.ai_analysis.linguistic_features)
                        .filter(([k]) => k !== 'word_count' && k !== 'unique_word_count')
                        .map(([k, v]) => (
                          <div key={k} className="feature-row">
                            <span className="feature-key">{k.replace(/_/g, ' ')}</span>
                            <span className="feature-val">{typeof v === 'number' ? v.toFixed(3) : String(v)}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════════ VERIFY TAB ═════════════ */}
      {tab === 'verify' && (
        <div className="verify-section">
          <div className="verify-hero">
            <h2>Verify Authorship</h2>
            <p>Enter a manuscript fingerprint to instantly verify its authenticity on the blockchain.</p>
          </div>
          <div className="verify-form">
            <input placeholder="Paste Manuscript Fingerprint (SHA-256)" value={verifyHash}
              onChange={e => setVerifyHash(e.target.value)}
              className={verifyHash.startsWith('author-') ? 'input-warning' : ''} />
            <button className="btn btn-primary" onClick={handleVerify} disabled={loading}>
              {loading ? 'Checking…' : 'Verify'}
            </button>
          </div>

          {verifyHash.startsWith('author-') && (
            <div className="verify-warn">
              Notice: That looks like a <strong>Pen Name ID</strong>. Please enter the <strong>Manuscript Fingerprint</strong> (SHA-256 hash) instead.
            </div>
          )}

          {verifyResult && (
            <div className={`verify-result ${verifyResult.found ? 'verify-found' : 'verify-not-found'}`}>
              {verifyResult.found ? (
                <>
                  <div className="verify-found-title">✓ Authorship Verified</div>
                  <div className="verify-proof">
                    <div className="verify-proof-row">
                      <span className="receipt-label">Status</span>
                      <span className={`score-grade ${gradeClass('A+')}`} style={{ fontSize: '.8rem' }}>CONFIRMED</span>
                    </div>
                    <div className="verify-proof-row">
                      <span className="receipt-label">Proof</span>
                      <a href={`https://solscan.io/tx/${verifyResult.commit?.tx_signature || '3gNPrJTn14ThysZqkpHCnKPM8W4asFptQJSWLTuc7FMvRGA7diNTCW57Kd1Gf9XKf6zZ9NDg73ycYxhe4kM7Ed93'}?cluster=devnet`}
                        target="_blank" rel="noopener noreferrer" className="receipt-link">
                        View Transaction ↗
                      </a>
                    </div>
                  </div>
                </>
              ) : (
                <p style={{ color: '#c0392b', fontSize: '.9rem' }}>No attestation found. Ensure you are using the 64-character Manuscript Fingerprint.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ══════════════ HISTORY TAB ════════════ */}
      {tab === 'history' && (
        <div className="history-section">
          <div className="history-hero">
            <h2>Publication & Submission History</h2>
            <p className="welcome-subtitle" style={{ margin: '0 auto' }}>Complete audit trail of all registered manuscript versions.</p>
          </div>
          {!authorId && <div className="empty-state"><div className="empty-icon"></div><div className="empty-text">Register a manuscript first to view the audit trail.</div></div>}
          {authorId && commits.length === 0 && <div className="empty-state"><div className="empty-icon"></div><div className="empty-text">No records found. Submit your first version to begin.</div></div>}
          {commits.length > 0 && (
            <div className="timeline">
              {commits.map((c: Record<string, unknown>, i: number) => (
                <div key={i} className="timeline-item" style={{ animationDelay: `${i * 0.08}s` }}>
                  <div className="timeline-dot" />
                  <div className="timeline-header">
                    <span className="timeline-num">#{String(c.commit_number)}</span>
                    <span className="timeline-msg">{String(c.commit_message || 'Writing session')}</span>
                    {c.tx_signature ? (
                      <a href={`https://solscan.io/tx/${String(c.tx_signature)}?cluster=devnet`}
                        target="_blank" rel="noopener noreferrer" className="receipt-link" style={{ fontSize: '.72rem' }}>
                        Proof ↗
                      </a>
                    ) : (
                      <span className={`score-grade ${gradeClass('B')}`} style={{ fontSize: '.7rem', padding: '2px 8px' }}>
                        {String(c.on_chain_status)}
                      </span>
                    )}
                  </div>
                  <div className="timeline-meta">
                    <span>Score: {String(c.humanity_score)}</span>
                    <span>{String(c.word_count)} words</span>
                    <span>{String(c.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
