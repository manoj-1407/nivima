import React, { useState } from 'react';
import { Code2, Copy, Check, Terminal, ChevronRight } from 'lucide-react';

const CODE_SAMPLES: Record<string, string> = {
  python: `from nivima import NivimaClient

# Initialize with your API key
client = NivimaClient(api_key="nvma_your_key")

# Submit a dubbing job
job = client.jobs.create(
    video_file=open("lecture.mp4", "rb"),
    source_language="hi",
    target_languages=["te", "ta", "bn", "ml"],
    domain="edtech_stem",
    voice_clone=True,
    consent_acknowledged=True
)

# Poll status
import time
while job.status not in ("completed", "failed"):
    time.sleep(10)
    job.refresh()
    print(f"Pipeline: {job.status} — {job.pipeline_stage}")

# Download each language track
for track in job.output_tracks:
    print(f"{track.language}: SyncNet={track.syncnet_score:.1f}")
    track.download(f"./output/{track.language}.mp4")`,

  curl: `# Submit a dubbing job
curl -X POST https://api.nivima.in/api/v1/jobs \\
  -H "Authorization: Bearer nvma_your_key" \\
  -F "video=@lecture.mp4" \\
  -F "source_language=hi" \\
  -F "target_languages=te,ta,bn" \\
  -F "domain=edtech_stem" \\
  -F "consent_acknowledged=true"

# Poll job status
curl https://api.nivima.in/api/v1/jobs/{job_id} \\
  -H "Authorization: Bearer nvma_your_key"`,

  manifest: `# Download the 3DMM Animation Manifest for adaptive playback
curl https://api.nivima.in/api/v1/jobs/{job_id}/manifest/te \\
  -H "Authorization: Bearer nvma_your_key" \\
  -o telugu_blendshapes.json

# Use with your Three.js or Unity renderer
# The manifest auto-adapts to player.playbackRate at runtime
# — no re-render needed at 1.5× or 2.0× speed`,
};

export const ApiSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'python' | 'curl' | 'manifest'>('python');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(CODE_SAMPLES[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section
      id="api"
      style={{
        padding: '80px 24px 120px',
        maxWidth: 1100,
        margin: '0 auto'
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: 44 }}>
        <div
          className="badge-pill"
          style={{
            background: 'rgba(139, 92, 246, 0.12)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            color: 'var(--accent-violet)',
            marginBottom: 12
          }}
        >
          <Terminal size={14} />
          <span>REST API + Python SDK</span>
        </div>
        <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Build With Nivima in 10 Lines
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 640, margin: '0 auto', fontSize: '15px', lineHeight: 1.6 }}>
          Full REST API with OpenAPI spec. Python SDK with sync/async support. Webhook support for pipeline progress events. Rate limits start at 10 concurrent jobs.
        </p>
      </div>

      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: 'var(--card-shadow)'
        }}
      >
        {/* Tab bar */}
        <div
          style={{
            background: 'var(--bg-base)',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '12px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { id: 'python', label: 'Python SDK' },
              { id: 'curl', label: 'cURL / REST' },
              { id: 'manifest', label: '3DMM Manifest API' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  background: activeTab === tab.id ? 'var(--bg-surface-elevated)' : 'transparent',
                  color: activeTab === tab.id ? 'var(--accent-saffron)' : 'var(--text-muted)',
                  border: '1px solid ' + (activeTab === tab.id ? 'var(--border-highlight)' : 'transparent'),
                  padding: '6px 14px',
                  borderRadius: 6,
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={handleCopy}
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            {copied ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>

        {/* Code content */}
        <pre
          style={{
            margin: 0,
            padding: '28px',
            fontSize: '13px',
            color: '#e2e8f0',
            background: '#080d14',
            overflowX: 'auto',
            lineHeight: 1.7,
            minHeight: 320
          }}
        >
          <code>{CODE_SAMPLES[activeTab]}</code>
        </pre>
      </div>

      {/* Endpoint pills */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 16,
          marginTop: 32
        }}
      >
        {[
          { method: 'POST', path: '/api/v1/jobs', desc: 'Submit new dubbing job with video upload' },
          { method: 'GET',  path: '/api/v1/jobs/{id}', desc: 'Poll status + telemetry + per-chunk QC' },
          { method: 'GET',  path: '/api/v1/jobs/{id}/manifest/{lang}', desc: 'Download 3DMM blendshape animation manifest' },
          { method: 'POST', path: '/api/v1/voices', desc: 'Upload reference audio for voice cloning' },
          { method: 'GET',  path: '/api/v1/qc/queue', desc: 'Fetch chunks awaiting human QC review' },
          { method: 'POST', path: '/api/v1/qc/{chunk_id}/decision', desc: 'Approve or revert a QC flagged chunk' },
        ].map((ep, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px 16px',
              display: 'flex',
              gap: 12,
              alignItems: 'flex-start'
            }}
          >
            <span
              style={{
                background: ep.method === 'POST' ? 'rgba(249,115,22,0.15)' : 'rgba(56,189,248,0.15)',
                color: ep.method === 'POST' ? 'var(--accent-saffron)' : 'var(--accent-blue)',
                padding: '2px 8px',
                borderRadius: 4,
                fontSize: '11px',
                fontWeight: 700,
                flexShrink: 0,
                fontFamily: 'var(--font-mono)'
              }}
            >
              {ep.method}
            </span>
            <div>
              <code style={{ fontSize: '12px', color: 'var(--text-main)', fontWeight: 600 }}>
                {ep.path}
              </code>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 2 }}>
                {ep.desc}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* CTA Strip */}
      <div
        style={{
          marginTop: 48,
          background: 'linear-gradient(135deg, rgba(249,115,22,0.08), rgba(139,92,246,0.08))',
          border: '1px solid var(--border-highlight)',
          borderRadius: 'var(--radius-lg)',
          padding: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 20
        }}
      >
        <div>
          <h3 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 6 }}>
            Ready to dub 10 languages in parallel?
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            Free tier: 10 minutes/month. Creator tier: 2 hours/month.
            Enterprise: custom SLA + GPU allocation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <a
            href="https://github.com/manoj-1407/nivima"
            target="_blank"
            rel="noreferrer"
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)',
              padding: '12px 22px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '14px',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <Code2 size={16} />
            <span>View Docs & API Spec</span>
          </a>
          <button
            style={{
              background: 'linear-gradient(135deg, var(--accent-saffron), #ea580c)',
              border: 'none',
              color: '#fff',
              padding: '12px 24px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '14px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: 'var(--glow-saffron)'
            }}
          >
            <ChevronRight size={16} />
            <span>Request Early Access</span>
          </button>
        </div>
      </div>
    </section>
  );
};
