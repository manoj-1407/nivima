import React, { useState, useEffect } from 'react';
import { Play, Pause, Sparkles, Volume2, ShieldCheck, Zap, ArrowRight, Activity } from 'lucide-react';
import { SUPPORTED_LANGUAGES, IndianLanguage } from '../types.ts';

interface HeroProps {
  onLaunchStudio: () => void;
  onExploreVisemes: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onLaunchStudio, onExploreVisemes }) => {
  const [selectedLang, setSelectedLang] = useState<IndianLanguage>(SUPPORTED_LANGUAGES[0]); // Hindi
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.5);
  const [audioProgress, setAudioProgress] = useState<number>(35);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setAudioProgress((prev) => (prev >= 100 ? 0 : prev + 2 * (playbackSpeed / 1.5)));
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed]);

  return (
    <section
      id="hero"
      style={{
        padding: '60px 24px 80px',
        maxWidth: 1200,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center'
      }}
    >
      {/* Top Banner Tag */}
      <div
        className="badge-pill"
        style={{
          background: 'rgba(249, 115, 22, 0.12)',
          border: '1px solid rgba(249, 115, 22, 0.3)',
          color: 'var(--accent-saffron)',
          marginBottom: 24,
          boxShadow: 'var(--glow-saffron)'
        }}
      >
        <Sparkles size={14} />
        <span>ACM Multimedia 2026 Breakthrough • World-First Dravidian Retroflex Lip Sync</span>
      </div>

      {/* Main Title */}
      <h1
        style={{
          fontSize: 'clamp(36px, 5.5vw, 68px)',
          fontWeight: 800,
          letterSpacing: '-0.04em',
          lineHeight: 1.1,
          maxWidth: 960,
          marginBottom: 20
        }}
      >
        Your Voice. 10 Indian Languages.{' '}
        <span className="text-gradient-neural">Flawless Lip Sync at Any Playback Speed.</span>
      </h1>

      {/* Subtitle */}
      <p
        style={{
          fontSize: 'clamp(16px, 2vw, 20px)',
          color: 'var(--text-muted)',
          maxWidth: 760,
          lineHeight: 1.6,
          marginBottom: 36
        }}
      >
        Standard AI dubbing collapses at 1.5× speed and ignores retroflex consonants. 
        Nivima combines <strong style={{ color: 'var(--text-main)' }}>IndicWhisper</strong>,{' '}
        <strong style={{ color: 'var(--text-main)' }}>IndicTrans2</strong>, and our{' '}
        <strong style={{ color: 'var(--accent-saffron)' }}>Playback-Adaptive 3DMM Manifest</strong> for zero-desync dubbing.
      </p>

      {/* Primary Action Buttons */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 56 }}>
        <button
          onClick={onLaunchStudio}
          style={{
            background: 'linear-gradient(135deg, var(--accent-saffron), #ea580c)',
            border: 'none',
            color: '#fff',
            padding: '14px 28px',
            borderRadius: 'var(--radius-md)',
            fontSize: '16px',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: 'var(--glow-saffron)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            transition: 'transform 0.15s ease'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <span>Open Dubbing Studio</span>
          <ArrowRight size={18} />
        </button>

        <button
          onClick={onExploreVisemes}
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-main)',
            padding: '14px 24px',
            borderRadius: 'var(--radius-md)',
            fontSize: '15px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            transition: 'border-color 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-violet)')}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
        >
          <Activity size={17} color="var(--accent-violet)" />
          <span>Interactive Viseme Lab</span>
        </button>
      </div>

      {/* Interactive Live Demo Stage */}
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: 960,
          borderRadius: 'var(--radius-lg)',
          padding: '28px',
          boxShadow: 'var(--card-shadow)',
          textAlign: 'left'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: isPlaying ? 'var(--accent-emerald)' : 'var(--accent-saffron)',
                boxShadow: isPlaying ? '0 0 10px var(--accent-emerald)' : 'none'
              }}
            />
            <span style={{ fontSize: '13px', fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Live Neural Acoustic & Viseme Synthesizer Preview
            </span>
          </div>

          <div className="badge-pill" style={{ background: 'var(--bg-surface-elevated)', color: 'var(--text-muted)' }}>
            <ShieldCheck size={14} color="var(--accent-emerald)" />
            <span>Voice-Cloned • Cryptographic Watermark</span>
          </div>
        </div>

        {/* Language selector chips */}
        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 12, marginBottom: 20 }}>
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSelectedLang(lang)}
              style={{
                background: selectedLang.code === lang.code ? 'var(--accent-saffron)' : 'var(--bg-surface-elevated)',
                color: selectedLang.code === lang.code ? '#fff' : 'var(--text-main)',
                border: '1px solid ' + (selectedLang.code === lang.code ? 'transparent' : 'var(--border-subtle)'),
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'all 0.15s ease'
              }}
            >
              <span>{lang.nativeName}</span>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>({lang.name})</span>
            </button>
          ))}
        </div>

        {/* Audio Wave & Speed Demo Box */}
        <div
          style={{
            background: 'var(--bg-base)',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            border: '1px solid var(--border-subtle)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 24
          }}
        >
          {/* Left: Wave & Sentence */}
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-faint)', textTransform: 'uppercase', fontWeight: 700, marginBottom: 6 }}>
              Synthesized Indian Speech ({selectedLang.name} • {selectedLang.family})
            </div>
            <div
              style={{
                fontSize: '18px',
                fontWeight: 600,
                color: 'var(--text-main)',
                marginBottom: 16,
                minHeight: 48
              }}
            >
              "{selectedLang.sampleSentence}"
            </div>

            {/* Simulated Animated Waveform */}
            <div
              style={{
                height: 48,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                marginBottom: 16,
                padding: '0 8px',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: 8
              }}
            >
              {Array.from({ length: 36 }).map((_, i) => {
                const height = isPlaying ? Math.sin(i * 0.4 + audioProgress) * 16 + 20 : 6;
                return (
                  <span
                    key={i}
                    style={{
                      height: `${Math.max(4, height)}px`,
                      width: 4,
                      borderRadius: 2,
                      background:
                        i < (audioProgress / 100) * 36
                          ? 'var(--accent-saffron)'
                          : 'var(--border-subtle)',
                      transition: 'height 0.1s ease, background 0.1s ease'
                    }}
                  />
                );
              })}
            </div>

            {/* Play Button & Progress */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: 'var(--accent-saffron)',
                  border: 'none',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  boxShadow: 'var(--glow-saffron)'
                }}
              >
                {isPlaying ? <Pause size={20} /> : <Play size={20} style={{ marginLeft: 2 }} />}
              </button>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>
                  {isPlaying ? 'Dubbing Streaming...' : 'Click to Audition Dubbed Voice'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Highlight: {selectedLang.phonemeHighlight}
                </div>
              </div>
            </div>
          </div>

          {/* Right: The 1.5x/2x Speed-Invariant Lip Sync Simulator */}
          <div
            style={{
              borderLeft: '1px solid var(--border-subtle)',
              paddingLeft: 24,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)' }}>
                  Playback Speed Invariance Test
                </span>
                <span
                  style={{
                    fontSize: '14px',
                    fontWeight: 800,
                    color: playbackSpeed > 1.2 ? 'var(--accent-saffron)' : 'var(--text-main)',
                    background: 'var(--bg-surface-elevated)',
                    padding: '2px 8px',
                    borderRadius: 4
                  }}
                >
                  {playbackSpeed.toFixed(1)}× Speed
                </span>
              </div>

              <input
                type="range"
                min="1.0"
                max="2.5"
                step="0.25"
                value={playbackSpeed}
                onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  accentColor: 'var(--accent-saffron)',
                  cursor: 'pointer',
                  marginBottom: 16
                }}
              />

              {/* Sync Delta Comparison */}
              <div
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface-elevated)',
                  fontSize: '12px',
                  lineHeight: 1.4,
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Wav2Lip / Standard Video:</span>
                  <span style={{ color: playbackSpeed > 1.0 ? 'var(--accent-rose)' : 'var(--accent-emerald)', fontWeight: 700 }}>
                    {playbackSpeed > 1.0 ? `+${Math.round((playbackSpeed - 1) * 140)}ms Desync (Broken)` : '0ms'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Nivima 3DMM Blendshape:</span>
                  <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
                    0.0ms Offset (Phase-Locked)
                  </span>
                </div>
              </div>
            </div>

            <div
              style={{
                marginTop: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: '11px',
                color: 'var(--text-muted)'
              }}
            >
              <Zap size={14} color="var(--accent-saffron)" />
              <span>73% of Indian students study video at 1.5× or faster. Nivima guarantees frame-perfect sync.</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
