import React, { useState } from 'react';
import { RETROFLEX_VISEMES, VisemeBlendshape } from '../types.ts';
import { Microscope, AlertTriangle, CheckCircle, Sliders } from 'lucide-react';

export const PhonemeVisemeLab: React.FC = () => {
  const [selectedViseme, setSelectedViseme] = useState<VisemeBlendshape>(RETROFLEX_VISEMES[0]);

  return (
    <section
      id="phonemes"
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
            background: 'rgba(249, 115, 22, 0.12)',
            border: '1px solid rgba(249, 115, 22, 0.3)',
            color: 'var(--accent-saffron)',
            marginBottom: 12
          }}
        >
          <Microscope size={14} />
          <span>Core Novel Research • Dravidian Phonetics</span>
        </div>
        <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Dravidian Retroflex Viseme Mapping Lab
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 700, margin: '0 auto', fontSize: '15px', lineHeight: 1.6 }}>
          Western lip-sync models (Wav2Lip, MuseTalk, LatentSync) rely on the English CMU phoneset, which has <strong>zero representation</strong> for retroflex consonants (Telugu ట/డ/ణ, Tamil ட/ண/ழ). Nivima introduces the first dedicated 3DMM retroflex blendshape mapping.
        </p>
      </div>

      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '32px',
          boxShadow: 'var(--card-shadow)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 32
        }}
      >
        {/* Left Column: Selector & Linguistics */}
        <div>
          <div style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 14 }}>
            Select Indian Retroflex Consonant:
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
            {RETROFLEX_VISEMES.map((v) => {
              const isSelected = selectedViseme.name === v.name;
              return (
                <div
                  key={v.name}
                  onClick={() => setSelectedViseme(v)}
                  style={{
                    background: isSelected ? 'rgba(249, 115, 22, 0.1)' : 'var(--bg-surface-elevated)',
                    border: '1px solid ' + (isSelected ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                    borderRadius: 'var(--radius-sm)',
                    padding: '14px 18px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)' }}>
                      {v.symbol}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: isSelected ? 'var(--accent-saffron)' : 'var(--text-muted)' }}>
                      {v.name}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {v.description}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Western Limitation vs Nivima Fix */}
          <div
            style={{
              background: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '18px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-rose)', fontSize: '13px', fontWeight: 700, marginBottom: 8 }}>
              <AlertTriangle size={16} />
              <span>The Industry Blindspot:</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 14 }}>
              {selectedViseme.westernLimitation}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-emerald)', fontSize: '13px', fontWeight: 700, marginBottom: 6 }}>
              <CheckCircle size={16} />
              <span>Nivima 3DMM Solution:</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Activates sub-mandibular tension with lateral cheek raiser ({Math.round(selectedViseme.cheekRaiser * 100)}%) and tongue curl index ({Math.round(selectedViseme.tongueCurl * 100)}%), yielding native visual naturalness.
            </p>
          </div>
        </div>

        {/* Right Column: 3DMM Blendshape Weight Meters */}
        <div
          style={{
            background: 'var(--bg-base)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between'
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sliders size={18} color="var(--accent-saffron)" />
                <span style={{ fontSize: '15px', fontWeight: 700 }}>
                  3DMM Facial Blendshape Weights
                </span>
              </div>
              <span className="badge-pill" style={{ background: 'var(--bg-surface-elevated)', color: 'var(--text-main)', fontSize: '11px' }}>
                Normalized [0.0 – 1.0]
              </span>
            </div>

            {/* Blendshape Bars */}
            {[
              { label: 'Jaw Open (Mandible)', val: selectedViseme.jawOpen, color: '#38bdf8' },
              { label: 'Lip Pressor (Orbicularis Oris)', val: selectedViseme.lipPressor, color: '#fb923c' },
              { label: 'Cheek Raiser (Zygomaticus)', val: selectedViseme.cheekRaiser, color: '#f43f5e' },
              { label: 'Lip Tightener (Buccinator)', val: selectedViseme.lipTightener, color: '#a855f7' },
              { label: 'Retroflex Tongue Curl Index', val: selectedViseme.tongueCurl, color: '#10b981' }
            ].map((shape, idx) => (
              <div key={idx} style={{ marginBottom: 18 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, marginBottom: 6 }}>
                  <span>{shape.label}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: shape.color }}>
                    {shape.val.toFixed(2)}
                  </span>
                </div>
                <div
                  style={{
                    height: 10,
                    background: 'var(--bg-surface-elevated)',
                    borderRadius: 5,
                    overflow: 'hidden'
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${shape.val * 100}%`,
                      background: shape.color,
                      borderRadius: 5,
                      transition: 'width 0.3s ease'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Research Reference */}
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface-elevated)',
              fontSize: '12px',
              color: 'var(--text-muted)',
              lineHeight: 1.4,
              border: '1px solid var(--border-subtle)',
              marginTop: 20
            }}
          >
            <strong>Reference:</strong> Nivima Research Paper Draft §4.2 (Table 2: Dravidian Retroflex Viseme Mapping to ARKit / MediaPipe Face Mesh blendshapes).
          </div>
        </div>
      </div>
    </section>
  );
};
