import React, { useState } from 'react';
import { ShieldCheck, Check, AlertOctagon, Undo2, Award, Gauge } from 'lucide-react';
import confetti from 'canvas-confetti';

export const QCInspector: React.FC = () => {
  const [decision, setDecision] = useState<'approved' | 'reverted' | 'pending'>('pending');
  const [activeTab, setActiveTab] = useState<'split' | 'reanimated' | 'original'>('split');

  const handleApprove = () => {
    setDecision('approved');
    confetti({
      particleCount: 50,
      spread: 60,
      origin: { y: 0.7 }
    });
  };

  const handleRevert = () => {
    setDecision('reverted');
  };

  return (
    <section
      id="qc"
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
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: 'var(--accent-emerald)',
            marginBottom: 12
          }}
        >
          <ShieldCheck size={14} />
          <span>Human-In-The-Loop QA & Automated Gatekeeper</span>
        </div>
        <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Automated Quality Control & Inspector
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 700, margin: '0 auto', fontSize: '15px', lineHeight: 1.6 }}>
          Nivima never outputs distorted frames or unnatural faces. Every single chunk is mathematically scored across <strong>SyncNet</strong>, <strong>CSIM Identity</strong>, and <strong>PSNR Lip Mask</strong>. Chunks failing thresholds automatically revert to original frames.
        </p>
      </div>

      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '32px',
          boxShadow: 'var(--card-shadow)'
        }}
      >
        {/* Header telemetry */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>Chunk #04 Inspection: 01:24.400 → 01:28.950</span>
              <span className="badge-pill" style={{ background: 'var(--bg-surface-elevated)', color: 'var(--accent-saffron)' }}>
                Target: Telugu (తెలుగు)
              </span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Phoneme target: Retroflex Plosive [ʈ] • Scene: Frontal Clear
            </div>
          </div>

          {/* View mode toggle */}
          <div style={{ display: 'flex', gap: 6, background: 'var(--bg-base)', padding: 4, borderRadius: 'var(--radius-sm)' }}>
            {(['split', 'reanimated', 'original'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  background: activeTab === tab ? 'var(--bg-surface-elevated)' : 'transparent',
                  color: activeTab === tab ? 'var(--text-main)' : 'var(--text-muted)',
                  border: 'none',
                  padding: '6px 14px',
                  borderRadius: 6,
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {tab} View
              </button>
            ))}
          </div>
        </div>

        {/* Video / Frame Comparison Stage */}
        <div
          style={{
            background: 'var(--bg-base)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            marginBottom: 28,
            display: 'grid',
            gridTemplateColumns: activeTab === 'split' ? '1fr 1fr' : '1fr',
            minHeight: 260
          }}
        >
          {/* Left Frame: Original */}
          {(activeTab === 'split' || activeTab === 'original') && (
            <div style={{ position: 'relative', padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', borderRight: activeTab === 'split' ? '1px solid var(--border-subtle)' : 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge-pill" style={{ background: 'rgba(255,255,255,0.08)', color: '#fff' }}>
                  Original Source Frame (Hi)
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
                  Frame 2542 • 1080p
                </span>
              </div>

              {/* Simulated Face Outline Art */}
              <div style={{ textAlign: 'center', margin: '30px 0' }}>
                <div
                  style={{
                    width: 140,
                    height: 180,
                    borderRadius: '50% 50% 45% 45%',
                    border: '2px solid rgba(255,255,255,0.2)',
                    margin: '0 auto',
                    position: 'relative',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 70%)'
                  }}
                >
                  {/* Eyes */}
                  <div style={{ display: 'flex', gap: 36, marginBottom: 28 }}>
                    <div style={{ width: 14, height: 4, background: 'var(--text-muted)', borderRadius: 2 }} />
                    <div style={{ width: 14, height: 4, background: 'var(--text-muted)', borderRadius: 2 }} />
                  </div>
                  {/* Nose */}
                  <div style={{ width: 4, height: 16, background: 'var(--text-faint)', borderRadius: 2, marginBottom: 18 }} />
                  {/* Neutral Mouth */}
                  <div style={{ width: 36, height: 8, borderRadius: '4px 4px 8px 8px', border: '2px solid var(--text-muted)' }} />
                </div>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
                Speaker: Original Hindi Vocal Articulation
              </div>
            </div>
          )}

          {/* Right Frame: Reanimated */}
          {(activeTab === 'split' || activeTab === 'reanimated') && (
            <div style={{ position: 'relative', padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="badge-pill" style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--accent-saffron)' }}>
                  Nivima Reanimated (Te Dubbed)
                </span>
                <span style={{ fontSize: '12px', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                  PSNR 38.5 dB • CSIM 0.94
                </span>
              </div>

              {/* Simulated Reanimated Face with Retroflex mouth */}
              <div style={{ textAlign: 'center', margin: '30px 0' }}>
                <div
                  style={{
                    width: 140,
                    height: 180,
                    borderRadius: '50% 50% 45% 45%',
                    border: '2px solid var(--accent-saffron)',
                    margin: '0 auto',
                    position: 'relative',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: 'var(--glow-saffron)',
                    background: 'radial-gradient(circle, rgba(249,115,22,0.06) 0%, transparent 70%)'
                  }}
                >
                  {/* Eyes (identical for face identity retention) */}
                  <div style={{ display: 'flex', gap: 36, marginBottom: 28 }}>
                    <div style={{ width: 14, height: 4, background: 'var(--text-muted)', borderRadius: 2 }} />
                    <div style={{ width: 14, height: 4, background: 'var(--text-muted)', borderRadius: 2 }} />
                  </div>
                  {/* Nose */}
                  <div style={{ width: 4, height: 16, background: 'var(--text-faint)', borderRadius: 2, marginBottom: 14 }} />
                  {/* Retroflex Mouth with Activated Cheek Tension */}
                  <div
                    style={{
                      width: 44,
                      height: 16,
                      borderRadius: '6px 6px 12px 12px',
                      background: 'rgba(249, 115, 22, 0.25)',
                      border: '2px solid var(--accent-saffron)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {/* Retroflex sub-apical tongue arc */}
                    <div style={{ width: 18, height: 4, background: '#ea580c', borderRadius: 2 }} />
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--accent-saffron)', textAlign: 'center', fontWeight: 600 }}>
                Synthesized Telugu Retroflex [ʈ] Lip & Cheek Shape
              </div>
            </div>
          )}
        </div>

        {/* Telemetry Scores Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 28 }}>
          <div style={{ background: 'var(--bg-surface-elevated)', padding: 16, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>
              <Gauge size={14} color="var(--accent-emerald)" />
              <span>SyncNet Score</span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--accent-emerald)' }}>
              8.4 <span style={{ fontSize: '13px', color: 'var(--text-faint)' }}>/ 10</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--accent-emerald)' }}>
              Pass threshold: &gt; 5.0 (Broadcast grade)
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-elevated)', padding: 16, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>
              <Award size={14} color="var(--accent-blue)" />
              <span>CSIM Face Identity</span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--accent-blue)' }}>
              0.94 <span style={{ fontSize: '13px', color: 'var(--text-faint)' }}>/ 1.0</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--accent-blue)' }}>
              Min threshold: &gt; 0.80 (Zero distortion)
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface-elevated)', padding: 16, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', color: 'var(--text-muted)', marginBottom: 4 }}>
              <ShieldCheck size={14} color="var(--accent-violet)" />
              <span>PSNR Non-Lip Skin</span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--accent-violet)' }}>
              38.5 dB
            </div>
            <div style={{ fontSize: '11px', color: 'var(--accent-violet)' }}>
              Min threshold: &gt; 30 dB (No skin blur)
            </div>
          </div>
        </div>

        {/* Human Decisions Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {decision === 'approved' && (
              <span className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
                <Check size={14} /> Approved for Export
              </span>
            )}
            {decision === 'reverted' && (
              <span className="badge-pill" style={{ background: 'rgba(244, 63, 94, 0.15)', color: 'var(--accent-rose)' }}>
                <AlertOctagon size={14} /> Reverted to Original Video
              </span>
            )}
            {decision === 'pending' && (
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Automated gate passed. Ready for human sign-off.
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button
              onClick={handleRevert}
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                padding: '10px 18px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              <Undo2 size={15} />
              <span>Revert Chunk to Original</span>
            </button>

            <button
              onClick={handleApprove}
              style={{
                background: 'linear-gradient(135deg, var(--accent-emerald), #059669)',
                border: 'none',
                color: '#fff',
                padding: '10px 24px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              <Check size={16} />
              <span>Approve & Deliver Track</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
