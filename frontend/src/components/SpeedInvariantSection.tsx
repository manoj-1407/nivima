import { useState } from 'react';
import { FastForward, CheckCircle, XCircle, Code2, Copy, Check } from 'lucide-react';
import { MeshVisualizerCanvas } from './MeshVisualizerCanvas.tsx';

export const SpeedInvariantSection = () => {
  const [copied, setCopied] = useState<boolean>(false);

  const manifestJson = `{
  "manifest_version": "1.0",
  "media_id": "job_01h8x9p2kqw7z",
  "source_language": "hi",
  "target_language": "te",
  "base_fps": 30.0,
  "duration_seconds": 272.4,
  "renderer": "3dmm_playback_adaptive",
  "continuous_spline_engine": "hermite_c1",
  "segments": [
    {
      "start_ms": 1240,
      "end_ms": 1890,
      "phoneme": "ʈ",
      "viseme": "RETROFLEX_STOP",
      "blendshape_weights": {
        "jaw_open": 0.38,
        "lip_pressor": 0.15,
        "cheek_raiser": 0.65,
        "tongue_curl": 0.95,
        "buccal_tension": 0.70
      },
      "tangents": {
        "in_velocity": [0.12, 0.05, 0.40, 0.85],
        "out_velocity": [-0.10, -0.02, -0.35, -0.80]
      },
      "time_scale_invariant": true
    }
  ]
}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(manifestJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section
      id="speed"
      style={{
        padding: '80px 24px',
        maxWidth: 1100,
        margin: '0 auto'
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: 44 }}>
        <div
          className="badge-pill"
          style={{
            background: 'rgba(56, 189, 248, 0.12)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: 'var(--accent-blue)',
            marginBottom: 12
          }}
        >
          <FastForward size={14} />
          <span>Patent-Pending Innovation • Playback Invariance</span>
        </div>
        <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Why Standard AI Dubbing Fails at 1.5× Speed
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 700, margin: '0 auto', fontSize: '15px', lineHeight: 1.6 }}>
          <strong>73% of Indian students</strong> watch educational and technical tutorials at 1.5×, 1.75×, or 2.0×. Existing video reanimation models bake lips into static 24fps MP4s. When the video player accelerates playback, phoneme-viseme coherence breaks down.
        </p>
      </div>

      {/* Embedded Live 3DMM Continuous Spline Canvas Simulator */}
      <div style={{ marginBottom: 36 }}>
        <MeshVisualizerCanvas initialSpeed={1.75} />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 28,
          marginBottom: 36
        }}
      >
        {/* Comparison: Traditional vs Nivima */}
        <div
          className="glass-panel"
          style={{
            borderRadius: 'var(--radius-md)',
            padding: '28px',
            border: '1px solid rgba(244, 63, 94, 0.25)',
            background: 'rgba(244, 63, 94, 0.02)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--accent-rose)', marginBottom: 16 }}>
            <XCircle size={22} />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Legacy AI Dubbing (HeyGen, Wav2Lip)</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 12, fontSize: '13px', color: 'var(--text-muted)' }}>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-rose)' }}>✕</span>
              <span><strong>Fixed-Frame Rasterization:</strong> Lip motion is permanently encoded as flat pixels at 1× playback.</span>
            </li>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-rose)' }}>✕</span>
              <span><strong>Desync Drift:</strong> Audio time-stretching creates phase lag (+180ms at 2× speed).</span>
            </li>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-rose)' }}>✕</span>
              <span><strong>Uncanny Jitter:</strong> Frame decimation causes unnatural mouth snapping and artifact strobing.</span>
            </li>
          </ul>
        </div>

        <div
          className="glass-panel"
          style={{
            borderRadius: 'var(--radius-md)',
            padding: '28px',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            background: 'rgba(16, 185, 129, 0.02)',
            boxShadow: 'var(--glow-violet)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--accent-emerald)', marginBottom: 16 }}>
            <CheckCircle size={22} />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Nivima Adaptive 3DMM Architecture</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 12, fontSize: '13px', color: 'var(--text-muted)' }}>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-emerald)' }}>✓</span>
              <span><strong>Time-Scale Invariant Manifests:</strong> Exports parametric blendshape tracks executed client-side.</span>
            </li>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-emerald)' }}>✓</span>
              <span><strong>Zero-Desync Lock:</strong> Blendshapes interpolate dynamically to match the active player clock.</span>
            </li>
            <li style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--accent-emerald)' }}>✓</span>
              <span><strong>Retroflex Fidelity:</strong> Retains full sub-apical tongue and jaw tension even at 2.5× velocity.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Manifest JSON Previewer */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          boxShadow: 'var(--card-shadow)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '13px', fontWeight: 700 }}>
            <Code2 size={16} color="var(--accent-saffron)" />
            <span>Nivima Animation Manifest JSON (IEEE & ACM Spec)</span>
          </div>
          <button
            onClick={handleCopy}
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)',
              padding: '6px 12px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            {copied ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy Spec'}</span>
          </button>
        </div>

        <pre
          style={{
            background: 'var(--bg-base)',
            padding: '20px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            color: 'var(--accent-saffron-light)',
            overflowX: 'auto',
            border: '1px solid var(--border-subtle)',
            lineHeight: 1.5
          }}
        >
          {manifestJson}
        </pre>
      </div>
    </section>
  );
};
