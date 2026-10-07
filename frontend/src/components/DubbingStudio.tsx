import { useState } from 'react';
import {
  Upload,
  CheckCircle2,
  Play,
  RotateCcw,
  Sliders,
  Layers,
  Shield,
  FileCheck,
  Check,
  Cpu,
  Download,
  Activity
} from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../types.ts';
import confetti from 'canvas-confetti';

export const DubbingStudio = () => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedFile] = useState<string | null>('edtech_physics_lecture_optics.mp4');
  const [sourceLang, setSourceLang] = useState<string>('hi');
  const [targetLangs, setTargetLangs] = useState<string[]>(['te', 'ta', 'bn']);
  const [domain, setDomain] = useState<string>('edtech_stem');
  const [consentAcknowledged, setConsentAcknowledged] = useState<boolean>(true);

  // Pipeline execution state
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [pipelineProgress, setPipelineProgress] = useState<number>(100);
  const [activePipelineStage, setActivePipelineStage] = useState<number>(6);

  const toggleTargetLang = (code: string) => {
    if (targetLangs.includes(code)) {
      if (targetLangs.length > 1) {
        setTargetLangs(targetLangs.filter((l) => l !== code));
      }
    } else {
      setTargetLangs([...targetLangs, code]);
    }
  };

  const handleStartDubbing = () => {
    setIsProcessing(true);
    setCurrentStep(3);
    setPipelineProgress(10);
    setActivePipelineStage(0);

    const stages = [
      { step: 1, progress: 25 },
      { step: 2, progress: 45 },
      { step: 3, progress: 65 },
      { step: 4, progress: 80 },
      { step: 5, progress: 92 },
      { step: 6, progress: 100 }
    ];

    stages.forEach((s, idx) => {
      setTimeout(() => {
        setActivePipelineStage(s.step);
        setPipelineProgress(s.progress);
        if (idx === stages.length - 1) {
          setIsProcessing(false);
          setCurrentStep(4);
          confetti({
            particleCount: 80,
            spread: 70,
            origin: { y: 0.6 }
          });
        }
      }, (idx + 1) * 1200);
    });
  };

  return (
    <section
      id="studio"
      style={{
        padding: '60px 24px 100px',
        maxWidth: 1100,
        margin: '0 auto'
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div
          className="badge-pill"
          style={{
            background: 'rgba(139, 92, 246, 0.12)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            color: 'var(--accent-violet)',
            marginBottom: 12
          }}
        >
          <Cpu size={14} />
          <span>Nivima Neural Dubbing Studio</span>
        </div>
        <h2 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Full-Stack Indic Dubbing Workflow
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: 640, margin: '0 auto', fontSize: '15px' }}>
          Upload your media, select Indic languages, verify speaker consent, and inspect the real-time neural pipeline with automated QC gating.
        </p>
      </div>

      {/* Stepper Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 36,
          position: 'relative'
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: 40,
            right: 40,
            height: 2,
            background: 'var(--border-subtle)',
            zIndex: 1
          }}
        />
        {[
          { num: 1, label: 'Upload & Video Ingest' },
          { num: 2, label: 'Languages & Consent' },
          { num: 3, label: 'Neural Pipeline' },
          { num: 4, label: 'QC & Multitrack Delivery' }
        ].map((step) => {
          const isActive = currentStep === step.num;
          const isDone = currentStep > step.num;
          return (
            <div
              key={step.num}
              style={{
                position: 'relative',
                zIndex: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer'
              }}
              onClick={() => !isProcessing && setCurrentStep(step.num)}
            >
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  background: isDone
                    ? 'var(--accent-emerald)'
                    : isActive
                    ? 'var(--accent-saffron)'
                    : 'var(--bg-surface-elevated)',
                  color: isDone || isActive ? '#fff' : 'var(--text-muted)',
                  border: '2px solid ' + (isActive ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '14px',
                  boxShadow: isActive ? 'var(--glow-saffron)' : 'none',
                  transition: 'all 0.2s'
                }}
              >
                {isDone ? <Check size={18} /> : step.num}
              </div>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--text-main)' : 'var(--text-muted)'
                }}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Main Step Body */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '36px',
          boxShadow: 'var(--card-shadow)',
          minHeight: 460
        }}
      >
        {/* STEP 1: UPLOAD */}
        {currentStep === 1 && (
          <div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: 8 }}>
              Step 1: Ingest Source Video
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: 24 }}>
              Supported formats: MP4, MOV, MKV. Demucs automatically extracts isolated vocals and stereo background audio stems.
            </p>

            <div
              style={{
                border: '2px dashed var(--border-highlight)',
                borderRadius: 'var(--radius-md)',
                padding: '48px 24px',
                textAlign: 'center',
                background: 'rgba(139, 92, 246, 0.03)',
                cursor: 'pointer',
                marginBottom: 24
              }}
            >
              <Upload size={40} color="var(--accent-violet)" style={{ marginBottom: 12 }} />
              <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: 4 }}>
                {selectedFile ? selectedFile : 'Drag and drop video file or click to browse'}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                1080p / 4K • 24–60 FPS • Stereo Audio • Up to 2 hours
              </div>
            </div>

            {/* Video metadata pill review */}
            {selectedFile && (
              <div
                style={{
                  background: 'var(--bg-surface-elevated)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 32,
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', gap: 20 }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>Duration</div>
                    <div style={{ fontSize: '14px', fontWeight: 600 }}>04m 32s (272s)</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>Resolution</div>
                    <div style={{ fontSize: '14px', fontWeight: 600 }}>1920×1080 (1080p)</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>Audio Codec</div>
                    <div style={{ fontSize: '14px', fontWeight: 600 }}>AAC 48kHz Stereo</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>Face Quality</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-emerald)' }}>Frontal Clear (96.4%)</div>
                  </div>
                </div>
                <div className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
                  <CheckCircle2 size={14} />
                  <span>Validation Passed</span>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setCurrentStep(2)}
                style={{
                  background: 'var(--accent-saffron)',
                  color: '#fff',
                  border: 'none',
                  padding: '12px 28px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '14px',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                Proceed to Language & Consent →
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: LANGUAGES & CONSENT */}
        {currentStep === 2 && (
          <div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: 8 }}>
              Step 2: Languages, Domain Adapter & Speaker Consent
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: 24 }}>
              Select target languages and domain glossary to preserve physics, biology, and mathematical terminology.
            </p>

            {/* Source & Domain */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: 6 }}>
                  Source Language:
                </label>
                <select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '14px',
                    fontWeight: 600
                  }}
                >
                  {SUPPORTED_LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.name} ({l.nativeName})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: 6 }}>
                  Domain Terminology Adapter:
                </label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '14px',
                    fontWeight: 600
                  }}
                >
                  <option value="edtech_stem">EdTech / STEM (Preserves velocity, refraction, integrals)</option>
                  <option value="medical">Medical & Clinical Terminology</option>
                  <option value="legal">Legal & Statutory Vocabulary</option>
                  <option value="general">Conversational & Entertainment</option>
                </select>
              </div>
            </div>

            {/* Target Languages Multi-select */}
            <div style={{ marginBottom: 28 }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: 10 }}>
                Target Indic Dubbing Languages ({targetLangs.length} Selected):
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {SUPPORTED_LANGUAGES.filter((l) => l.code !== sourceLang).map((l) => {
                  const isSelected = targetLangs.includes(l.code);
                  return (
                    <button
                      key={l.code}
                      onClick={() => toggleTargetLang(l.code)}
                      style={{
                        background: isSelected ? 'rgba(249, 115, 22, 0.15)' : 'var(--bg-surface-elevated)',
                        color: isSelected ? 'var(--accent-saffron)' : 'var(--text-muted)',
                        border: '1px solid ' + (isSelected ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                        padding: '8px 16px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8
                      }}
                    >
                      <span>{l.nativeName}</span>
                      <span style={{ fontSize: '12px' }}>{l.name}</span>
                      {isSelected && <Check size={14} />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Biometric Voice Cloning Consent */}
            <div
              style={{
                background: 'rgba(249, 115, 22, 0.04)',
                border: '1px solid rgba(249, 115, 22, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                marginBottom: 32
              }}
            >
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <Shield size={24} color="var(--accent-saffron)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700, marginBottom: 4 }}>
                    Speaker Biometric Voice-Cloning Consent & Digital Watermark
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 12 }}>
                    Nivima embeds an imperceptible cryptographic audio watermark (ITU-R BS.1116 compliant) verifying legitimate owner authorization and preventing non-consensual deepfakes.
                  </p>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}>
                    <input
                      type="checkbox"
                      checked={consentAcknowledged}
                      onChange={(e) => setConsentAcknowledged(e.target.checked)}
                      style={{ width: 16, height: 16, accentColor: 'var(--accent-saffron)' }}
                    />
                    <span>I confirm I own or have legal authorization to clone this speaker's voice across all target languages.</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button
                onClick={() => setCurrentStep(1)}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-muted)',
                  padding: '12px 24px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                ← Back
              </button>
              <button
                disabled={!consentAcknowledged || targetLangs.length === 0}
                onClick={handleStartDubbing}
                style={{
                  background: 'linear-gradient(135deg, var(--accent-saffron), #ea580c)',
                  color: '#fff',
                  border: 'none',
                  padding: '12px 32px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '15px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  opacity: !consentAcknowledged || targetLangs.length === 0 ? 0.5 : 1,
                  boxShadow: 'var(--glow-saffron)'
                }}
              >
                Dispatch Neural Dubbing Pipeline 🚀
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: PIPELINE EXECUTION */}
        {currentStep === 3 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: 4 }}>
                  Step 3: Neural Pipeline Execution & Telemetry
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                  GPU Cluster device: NVIDIA RTX 4090 • Zero-desync 3DMM renderer active
                </p>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-saffron)' }}>
                {pipelineProgress}%
              </div>
            </div>

            {/* Progress bar */}
            <div
              style={{
                height: 8,
                background: 'var(--bg-surface-elevated)',
                borderRadius: 4,
                overflow: 'hidden',
                marginBottom: 32
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${pipelineProgress}%`,
                  background: 'linear-gradient(90deg, var(--accent-saffron), var(--accent-violet))',
                  transition: 'width 0.4s ease'
                }}
              />
            </div>

            {/* Pipeline Stage Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginBottom: 32 }}>
              {[
                { title: '1. Demucs Stem Split', desc: 'Isolating vocals from background audio', icon: Layers },
                { title: '2. IndicWhisper ASR', desc: 'Extracting word & phoneme timestamps', icon: Sliders },
                { title: '3. IndicTrans2 + Llama', desc: 'Domain-constrained semantic translation', icon: FileCheck },
                { title: '4. XTTS-v2 Cross-Lingual', desc: 'Cloning timbre and pitch curve', icon: Play },
                { title: '5. MFA & 3DMM Manifest', desc: 'Dravidian retroflex viseme blendshapes', icon: Activity },
                { title: '6. Automated QC Gate', desc: 'SyncNet, CSIM, and PSNR verification', icon: Shield }
              ].map((stage, idx) => {
                const isStageComplete = activePipelineStage > idx;
                const isStageCurrent = activePipelineStage === idx;
                const IconComponent = stage.icon;

                return (
                  <div
                    key={idx}
                    style={{
                      background: isStageCurrent
                        ? 'rgba(249, 115, 22, 0.08)'
                        : isStageComplete
                        ? 'var(--bg-surface-elevated)'
                        : 'var(--bg-base)',
                      border:
                        '1px solid ' +
                        (isStageCurrent
                          ? 'var(--accent-saffron)'
                          : isStageComplete
                          ? 'rgba(16, 185, 129, 0.3)'
                          : 'var(--border-subtle)'),
                      borderRadius: 'var(--radius-sm)',
                      padding: '16px',
                      display: 'flex',
                      gap: 12,
                      alignItems: 'center'
                    }}
                  >
                    <div
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 8,
                        background: isStageComplete
                          ? 'var(--accent-emerald)'
                          : isStageCurrent
                          ? 'var(--accent-saffron)'
                          : 'var(--bg-surface)',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {isStageComplete ? <Check size={18} /> : <IconComponent size={18} />}
                    </div>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)' }}>
                        {stage.title}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {isStageComplete ? 'Completed • Validated' : isStageCurrent ? 'Processing...' : stage.desc}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* STEP 4: OUTPUT & MULTITRACK DELIVERY */}
        {currentStep === 4 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <div className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', marginBottom: 8 }}>
                  <CheckCircle2 size={14} />
                  <span>QC Passed • Broadcast Grade</span>
                </div>
                <h3 style={{ fontSize: '24px', fontWeight: 800 }}>
                  Dubbed Media Ready for Distribution
                </h3>
              </div>
              <button
                onClick={() => {
                  setCurrentStep(1);
                  setPipelineProgress(0);
                }}
                style={{
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <RotateCcw size={14} />
                <span>New Dubbing Job</span>
              </button>
            </div>

            {/* Output Delivery Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 32 }}>
              {targetLangs.map((langCode) => {
                const lang = SUPPORTED_LANGUAGES.find((l) => l.code === langCode);
                if (!lang) return null;

                return (
                  <div
                    key={langCode}
                    style={{
                      background: 'var(--bg-base)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '20px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span style={{ fontSize: '16px', fontWeight: 700 }}>
                          {lang.name} ({lang.nativeName})
                        </span>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 8px', borderRadius: 4 }}>
                          SyncNet 8.4
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 16 }}>
                        Track: Cloned Vocal + Original Demucs Background SFX (48kHz AAC)
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 10 }}>
                      <button
                        style={{
                          flex: 1,
                          background: 'var(--accent-saffron)',
                          border: 'none',
                          color: '#fff',
                          padding: '10px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '13px',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 6
                        }}
                      >
                        <Play size={14} />
                        <span>Audition Video</span>
                      </button>

                      <button
                        style={{
                          background: 'var(--bg-surface-elevated)',
                          border: '1px solid var(--border-subtle)',
                          color: 'var(--text-main)',
                          padding: '10px 14px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '13px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6
                        }}
                      >
                        <Download size={14} />
                        <span>MP4 + Manifest</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
