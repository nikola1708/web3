'use client';
import { useState, useRef } from 'react';

const API = 'http://localhost:8000';

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
  const fileRef = useRef<HTMLInputElement>(null);

  const ensureAuthor = () => {
    if (!authorId) {
      const id = 'author-' + Math.random().toString(36).slice(2, 10);
      setAuthorId(id);
      return id;
    }
    return authorId;
  };

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError('');
    setResult(null);

    const aid = ensureAuthor();
    const form = new FormData();
    form.append('file', file);
    form.append('author_id', aid);
    if (documentId) form.append('document_id', documentId);
    if (title) form.append('title', title);
    if (commitMessage) form.append('commit_message', commitMessage);

    try {
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Upload failed');
      }
      const data: AnalysisResult = await res.json();
      setResult(data);
      setDocumentId(data.document_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verifyHash.trim()) return;
    setLoading(true);
    setVerifyResult(null);
    setError('');

    try {
      const res = await fetch(`${API}/api/verify/${verifyHash.trim()}`);
      const data: VerifyResult = await res.json();
      setVerifyResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    if (!authorId) return;
    try {
      const res = await fetch(`${API}/api/authors/${authorId}/commits`);
      const data = await res.json();
      setCommits(data);
    } catch {
      setCommits([]);
    }
  };

  const gradeClass = (grade: string) => {
    if (grade.startsWith('A')) return 'grade-a';
    if (grade === 'B') return 'grade-b';
    if (grade === 'C') return 'grade-c';
    if (grade === 'D') return 'grade-d';
    if (grade === 'E') return 'grade-e';
    return 'grade-f';
  };

  return (
    <div className="container">
      <h1>🐰 Bunny</h1>
      <p className="subtitle">Digital Heartbeat for Writers — Prove your work is human-authored</p>

      <div className="tabs">
        <button className={`tab ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
          Upload & Analyze
        </button>
        <button className={`tab ${tab === 'verify' ? 'active' : ''}`} onClick={() => setTab('verify')}>
          Verify Hash
        </button>
        <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => { setTab('history'); loadHistory(); }}>
          Commit History
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {/* ── Upload Tab ─────────────────────────────── */}
      {tab === 'upload' && (
        <>
          <div
            className={`upload-section ${dragover ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragover(false);
              const f = e.dataTransfer.files[0];
              if (f) handleUpload(f);
            }}
          >
            <p>📄 Drag & drop your manuscript here, or click to select</p>
            <p style={{ color: '#666', fontSize: '0.8rem', marginTop: 8 }}>
              Supported: .docx, .md, .pdf, .txt
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".docx,.doc,.md,.pdf,.txt"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
              }}
              style={{ marginTop: 12 }}
            />
          </div>

          <div className="form-group">
            <input
              placeholder="Author ID (auto-generated if empty)"
              value={authorId}
              onChange={(e) => setAuthorId(e.target.value)}
            />
            <input
              placeholder="Document ID (for subsequent commits)"
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
            />
          </div>
          <div className="form-group">
            <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <input
              placeholder="Commit message"
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
            />
          </div>

          {loading && (
            <div className="loading">
              <div className="spinner" />
              Analyzing manuscript...
            </div>
          )}

          {result && (
            <div className="results">
              {/* Humanity Score */}
              <div className="result-card">
                <h3>Humanity Score</h3>
                <div className="score-display">
                  <span className="score-big">{result.humanity.humanity_score.toFixed(1)}</span>
                  <span className={`grade-badge ${gradeClass(result.humanity.grade)}`}>
                    {result.humanity.grade}
                  </span>
                  <span style={{ color: '#aaa' }}>{result.humanity.label}</span>
                </div>
              </div>

              {/* Hash */}
              <div className="result-card">
                <h3>Manuscript Fingerprint (SHA-256)</h3>
                <div className="hash-display">{result.manuscript_hash}</div>
                {result.commit && (
                  <p style={{ marginTop: 8, color: '#888', fontSize: '0.85rem' }}>
                    Commit #{result.commit.commit_number} • On-chain: {result.commit.on_chain_status}
                    {result.document_id && ` • Doc: ${result.document_id.slice(0, 8)}...`}
                  </p>
                )}
              </div>

              {/* Stats */}
              <div className="result-card">
                <h3>Text Statistics</h3>
                <div className="stat-grid">
                  <div className="stat-item">
                    <div className="stat-value">{result.text_stats.word_count?.toLocaleString()}</div>
                    <div className="stat-label">Words</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{result.text_stats.sentence_count}</div>
                    <div className="stat-label">Sentences</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{result.text_stats.paragraph_count}</div>
                    <div className="stat-label">Paragraphs</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{result.text_stats.avg_sentence_length?.toFixed(1)}</div>
                    <div className="stat-label">Avg Sentence Len</div>
                  </div>
                </div>
              </div>

              {/* AI Analysis */}
              <div className="result-card">
                <h3>AI Detection ({result.ai_analysis.model_used})</h3>
                <div className="stat-grid">
                  <div className="stat-item">
                    <div className="stat-value">{result.ai_analysis.ai_score.toFixed(1)}%</div>
                    <div className="stat-label">AI Probability</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{(result.ai_analysis.confidence * 100).toFixed(0)}%</div>
                    <div className="stat-label">Confidence</div>
                  </div>
                </div>
                <h3 style={{ marginTop: 16 }}>Linguistic Features</h3>
                <div className="features-grid">
                  {Object.entries(result.ai_analysis.linguistic_features)
                    .filter(([k]) => k !== 'word_count' && k !== 'unique_word_count')
                    .map(([k, v]) => (
                      <div key={k} className="feature-item">
                        <span className="feature-label">{k.replace(/_/g, ' ')}</span>
                        <span className="feature-value">
                          {typeof v === 'number' ? v.toFixed(3) : String(v)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Temporal */}
              <div className="result-card">
                <h3>Temporal Analysis</h3>
                <div className="stat-grid">
                  <div className="stat-item">
                    <div className="stat-value">{result.temporal_analysis.temporal_score.toFixed(1)}</div>
                    <div className="stat-label">Temporal Score</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{result.temporal_analysis.total_commits}</div>
                    <div className="stat-label">Previous Commits</div>
                  </div>
                </div>
                <p style={{ marginTop: 8, color: '#888', fontSize: '0.85rem' }}>
                  {result.temporal_analysis.analysis}
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Verify Tab ─────────────────────────────── */}
      {tab === 'verify' && (
        <div className="verify-section">
          <h2>Verify a Manuscript</h2>
          <p style={{ color: '#888', marginBottom: 16 }}>
            Enter a SHA-256 hash to check if it has been attested.
          </p>
          <div className="verify-input">
            <input
              placeholder="SHA-256 hash (64 hex characters)"
              value={verifyHash}
              onChange={(e) => setVerifyHash(e.target.value)}
            />
            <button className="btn-primary" onClick={handleVerify} disabled={loading}>
              {loading ? 'Checking...' : 'Verify'}
            </button>
          </div>

          {verifyResult && (
            <div className={`verify-result ${verifyResult.found ? 'verify-found' : 'verify-not-found'}`}>
              {verifyResult.found ? (
                <>
                  <p style={{ fontWeight: 700, color: '#34d399' }}>✓ Attestation Found</p>
                  <pre style={{ marginTop: 8, fontSize: '0.8rem', color: '#aaa', overflow: 'auto' }}>
                    {JSON.stringify(verifyResult.commit, null, 2)}
                  </pre>
                </>
              ) : (
                <p style={{ color: '#888' }}>No attestation found for this hash.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── History Tab ────────────────────────────── */}
      {tab === 'history' && (
        <div>
          <h2>Commit History</h2>
          {!authorId && <p style={{ color: '#888' }}>Upload a manuscript first to generate an author ID.</p>}
          {authorId && commits.length === 0 && (
            <p style={{ color: '#888' }}>No commits yet. Upload a manuscript to start.</p>
          )}
          <ul className="commit-list">
            {commits.map((c: Record<string, unknown>, i: number) => (
              <li key={i} className="commit-item">
                <span className="commit-number">#{String(c.commit_number)}</span>
                <div className="commit-info">
                  <div className="commit-msg">{String(c.commit_message || 'No message')}</div>
                  <div className="commit-meta">
                    Score: {String(c.humanity_score)} •
                    Words: {String(c.word_count)} •
                    {String(c.created_at)}
                  </div>
                </div>
                <span className={`grade-badge ${gradeClass('B')}`} style={{ fontSize: '0.8rem' }}>
                  {String(c.on_chain_status)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
