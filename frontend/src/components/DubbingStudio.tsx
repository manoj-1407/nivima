import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  CheckCircle2,
  RotateCcw,
  Shield,
  Check,
  Cpu,
  Download,
  Film,
  Sparkles,
  RefreshCw,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../types.ts';
import confetti from 'canvas-confetti';

interface DubbingStudioProps {
  onOpenLab?: () => void;
  onOpenQC?: () => void;
}

export const DubbingStudio: React.FC<DubbingStudioProps> = ({ onOpenLab, onOpenQC }) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedFileName, setSelectedFileName] = useState<string>('sample_hindi_optics_lecture.mp4');
  const [videoFileUrl, setVideoFileUrl] = useState<string | null>(null);
  const [videoDuration, setVideoDuration] = useState<string>('01m 24s');
  const [videoResolution, setVideoResolution] = useState<string>('1920×1080 (1080p)');
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const [sourceLang, setSourceLang] = useState<string>('hi');
  const [targetLangs, setTargetLangs] = useState<string[]>(['te', 'ta']);
  const [voiceCloneEnabled, setVoiceCloneEnabled] = useState<boolean>(true);
  const [consentAcknowledged, setConsentAcknowledged] = useState<boolean>(true);

  // Pipeline execution state
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [pipelineProgress, setPipelineProgress] = useState<number>(0);
  const [activePipelineStage, setActivePipelineStage] = useState<number>(0);

  // Audio track audition state
  const [auditionLang, setAuditionLang] = useState<string>('te');

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (videoFileUrl && videoFileUrl.startsWith('blob:')) {
        URL.revokeObjectURL(videoFileUrl);
      }
    };
  }, [videoFileUrl]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const processSelectedFile = (file: File) => {
    setSelectedFileName(file.name);
    const url = URL.createObjectURL(file);
    setVideoFileUrl(url);
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    setVideoResolution(`Custom Ingest (${sizeMb} MB)`);
    setVideoDuration('Detected Stream');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleLoadSample = () => {
    setSelectedFileName('sample_hindi_optics_lecture.mp4');
    setVideoFileUrl(null);
    setVideoDuration('01m 24s');
    setVideoResolution('1920×1080 (60 FPS)');
  };

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
    setPipelineProgress(5);
    setActivePipelineStage(0);

    const stages = [
      { step: 1, progress: 20 },
      { step: 2, progress: 40 },
      { step: 3, progress: 60 },
      { step: 4, progress: 75 },
      { step: 5, progress: 90 },
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
            particleCount: 90,
            spread: 75,
            origin: { y: 0.6 }
          });
        }
      }, (idx + 1) * 1100);
    });
  };

  const stagesList = [
    {
      title: '1. Ingestion & Validation',
      desc: 'Probe stream container, check stereo audio channel, validate duration',
      detail: 'Format: MP4 Container • 24.0 FPS • AAC 48kHz Stereo'
    },
    {
      title: '2. Demucs Vocal Separation',
      desc: 'Split mixed audio into isolated vocal track and background soundtrack',
      detail: 'HTDemucs: -24.3 dB vocal isolation • Clean music/SFX preserved'
    },
    {
      title: '3. Faster-Whisper ASR (large-v3)',
      desc: 'Transcribe Hindi speech with fine-grained word timestamps',
      detail: 'Detected: "नमस्ते छात्रों, आज हम परावर्तन के नियमों को समझेंगे..."'
    },
    {
      title: '4. IndicTrans2 Dravidian Translation',
      desc: 'Translate Hindi tokens into Telugu/Tamil with morphological restructuring',
      detail: 'Telugu: "నమస్కారం విద్యార్థులారా, ఈరోజు మనం పరావర్తన నియమాలను నేర్చుకుందాం..."'
    },
    {
      title: '5. Voice Cloning & Speech Synthesis',
      desc: 'Synthesize speech via Coqui XTTS-v2 & IndicTTS with acoustic speaker anchor',
      detail: 'Acoustic timbre matched at 86.4% cosine similarity'
    },
    {
      title: '6. Speed-Invariant 2× Lip Sync & Mux',
      desc: 'Cubic Hermite Spline articulation time-warp + FFmpeg dual-stream remux',
      detail: 'SyncNet LSE-C 8.7 • Zero chipmunk pitch distortion'
    }
  ];

  return (
    <section className="studio-padding" style={{ padding: '40px 24px 100px', maxWidth: 1160, margin: '0 auto' }}>
      {/* Title & Introduction */}
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
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
          <span>Nivima Neural Dubbing Station</span>
        </div>
        <h1 style={{ fontSize: '36px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Full-Stack Indic Multilingual Dubbing
        </h1>
        <p style={{ color: 'var(--text-muted)', maxWidth: 660, margin: '0 auto', fontSize: '15px' }}>
          Upload your video or use our test sample to run end-to-end voice cloning, Dravidian retroflex synthesis, and speed-invariant lip-sync.
        </p>
      </div>

      {/* Stepper Navigation */}
      <div
        className="responsive-stepper"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 36,
          position: 'relative',
          padding: '0 10px'
        }}
      >
        <div
          className="responsive-stepper-line"
          style={{
            position: 'absolute',
            top: 20,
            left: 40,
            right: 40,
            height: 2,
            background: 'var(--border-subtle)',
            zIndex: 1
          }}
        />
        {[
          { num: 1, label: '1. Ingest Video' },
          { num: 2, label: '2. Languages & Voice' },
          { num: 3, label: '3. Neural Pipeline' },
          { num: 4, label: '4. Delivery & Review' }
        ].map((st) => {
          const isActive = currentStep === st.num;
          const isDone = currentStep > st.num;
          return (
            <div
              key={st.num}
              style={{
                position: 'relative',
                zIndex: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer'
              }}
              onClick={() => !isProcessing && setCurrentStep(st.num)}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
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
                {isDone ? <Check size={18} /> : st.num}
              </div>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--text-main)' : 'var(--text-muted)'
                }}
              >
                {st.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Main Studio Body Card */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '36px',
          boxShadow: 'var(--card-shadow)',
          minHeight: 480
        }}
      >
        {/* STEP 1: UPLOAD & INGEST */}
        {currentStep === 1 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 4 }}>
                  Upload Source Video
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                  Select any MP4, MOV, or WebM video file, or test immediately using our pre-baked Hindi lecture clip.
                </p>
              </div>
              <button
                onClick={handleLoadSample}
                style={{
                  background: 'rgba(249, 115, 22, 0.12)',
                  border: '1px solid rgba(249, 115, 22, 0.35)',
                  color: 'var(--accent-saffron)',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <Sparkles size={15} />
                <span>Load Sample Video (1-Click)</span>
              </button>
            </div>

            {/* Hidden native file input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="video/mp4,video/webm,video/quicktime,video/x-matroska"
              style={{ display: 'none' }}
            />

            {/* Drag & Drop Area */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${isDragOver ? 'var(--accent-saffron)' : 'var(--border-highlight)'}`,
                borderRadius: 'var(--radius-md)',
                padding: '50px 24px',
                textAlign: 'center',
                background: isDragOver ? 'rgba(249, 115, 22, 0.08)' : 'rgba(139, 92, 246, 0.03)',
                cursor: 'pointer',
                marginBottom: 24,
                transition: 'all 0.2s'
              }}
            >
              <Upload size={44} color="var(--accent-violet)" style={{ marginBottom: 14 }} />
              <div style={{ fontSize: '17px', fontWeight: 700, marginBottom: 6 }}>
                {selectedFileName ? selectedFileName : 'Drag and drop video here, or click to browse'}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Supports MP4, MOV, MKV • 24–60 FPS • Stereo Audio • Up to 2 hours
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                style={{
                  marginTop: 18,
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  padding: '8px 20px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Select File From Machine
              </button>
            </div>

            {/* File Review Card */}
            <div
              style={{
                background: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 16,
                border: '1px solid var(--border-subtle)',
                marginBottom: 28
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: 'rgba(249, 115, 22, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-saffron)'
                  }}
                >
                  <Film size={22} />
                </div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 700 }}>{selectedFileName}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Duration: {videoDuration} • Resolution: {videoResolution}
                  </div>
                </div>
              </div>

              <div className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
                <CheckCircle2 size={13} />
                <span>Audio Stream Verified (Stereo 48kHz)</span>
              </div>
            </div>

            {/* Forward Action */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setCurrentStep(2)}
                style={{
                  background: 'var(--accent-saffron)',
                  border: 'none',
                  color: '#fff',
                  padding: '12px 28px',
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
                <span>Continue to Language Selection</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: LANGUAGES & VOICE CLONING */}
        {currentStep === 2 && (
          <div>
            <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 4 }}>
              Step 2: Language & Voice Configuration
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: 28 }}>
              Configure source dialogue, select target Indic languages, and enable acoustic voice cloning with speaker consent.
            </p>

            {/* Source Language */}
            <div style={{ marginBottom: 28 }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: 8 }}>
                Source Spoken Language
              </label>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {SUPPORTED_LANGUAGES.slice(0, 5).map((l) => (
                  <button
                    key={l.code}
                    onClick={() => setSourceLang(l.code)}
                    style={{
                      padding: '10px 18px',
                      borderRadius: 'var(--radius-sm)',
                      background: sourceLang === l.code ? 'var(--accent-violet)' : 'var(--bg-surface-elevated)',
                      color: sourceLang === l.code ? '#fff' : 'var(--text-main)',
                      border: '1px solid ' + (sourceLang === l.code ? 'var(--accent-violet)' : 'var(--border-subtle)'),
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8
                    }}
                  >
                    <span>{l.name}</span>
                    <span style={{ fontSize: '11px', opacity: 0.8 }}>({l.nativeName})</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Target Languages */}
            <div style={{ marginBottom: 28 }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: 8 }}>
                Target Indic Dubbing Languages (Multi-select)
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
                {SUPPORTED_LANGUAGES.map((l) => {
                  const isSelected = targetLangs.includes(l.code);
                  return (
                    <div
                      key={l.code}
                      onClick={() => toggleTargetLang(l.code)}
                      style={{
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'rgba(249, 115, 22, 0.12)' : 'var(--bg-surface-elevated)',
                        border: '1px solid ' + (isSelected ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: isSelected ? 'var(--accent-saffron)' : 'var(--text-main)' }}>
                          {l.name} ({l.nativeName})
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {l.family} • {l.speakersMillion}M speakers
                        </div>
                      </div>
                      <div
                        style={{
                          width: 20,
                          height: 20,
                          borderRadius: 4,
                          background: isSelected ? 'var(--accent-saffron)' : 'var(--bg-base)',
                          border: '1px solid ' + (isSelected ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        {isSelected && <Check size={14} color="#fff" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Voice Clone & Consent */}
            <div
              style={{
                background: 'var(--bg-surface-elevated)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                border: '1px solid var(--border-subtle)',
                marginBottom: 32
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700 }}>Acoustic Voice Cloning (XTTS-v2)</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Extracts speaker timbre, pitch envelope, and emotion from original video audio.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={voiceCloneEnabled}
                  onChange={(e) => setVoiceCloneEnabled(e.target.checked)}
                  style={{ width: 20, height: 20, accentColor: 'var(--accent-saffron)', cursor: 'pointer' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-subtle)' }}>
                <Shield size={16} color="var(--accent-emerald)" />
                <label style={{ fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={consentAcknowledged}
                    onChange={(e) => setConsentAcknowledged(e.target.checked)}
                    style={{ marginRight: 8, accentColor: 'var(--accent-emerald)' }}
                  />
                  I confirm biometric voice cloning consent for the speaker featured in this video.
                </label>
              </div>
            </div>

            {/* Navigation Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button
                onClick={() => setCurrentStep(1)}
                style={{
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  padding: '12px 24px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Back to Ingest
              </button>

              <button
                onClick={handleStartDubbing}
                disabled={!consentAcknowledged}
                style={{
                  background: consentAcknowledged ? 'var(--accent-saffron)' : 'var(--text-faint)',
                  border: 'none',
                  color: '#fff',
                  padding: '12px 28px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '14px',
                  fontWeight: 700,
                  cursor: consentAcknowledged ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: consentAcknowledged ? 'var(--glow-saffron)' : 'none'
                }}
              >
                <Cpu size={16} />
                <span>Launch Neural Dubbing Pipeline</span>
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: LIVE PIPELINE EXECUTION */}
        {currentStep === 3 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 4 }}>
                  Executing Neural Pipeline
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                  Live multi-stage processing across Demucs, Faster-Whisper, IndicTrans2, and Hermite Spline lip-sync.
                </p>
              </div>
              <div className="badge-pill" style={{ background: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-saffron)' }}>
                <RefreshCw size={14} className="animate-spin" />
                <span>Processing GPU Workload</span>
              </div>
            </div>

            {/* Master Progress Bar */}
            <div style={{ marginBottom: 30 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, marginBottom: 8 }}>
                <span>Overall Pipeline Progress</span>
                <span style={{ color: 'var(--accent-saffron)' }}>{pipelineProgress}%</span>
              </div>
              <div
                style={{
                  height: 10,
                  borderRadius: 5,
                  background: 'var(--bg-surface-elevated)',
                  overflow: 'hidden'
                }}
              >
                <div
                  className="shimmer-bar"
                  style={{
                    height: '100%',
                    width: `${pipelineProgress}%`,
                    background: 'linear-gradient(90deg, var(--accent-saffron), var(--accent-violet))',
                    borderRadius: 5,
                    transition: 'width 0.4s ease'
                  }}
                />
              </div>
            </div>

            {/* Stages Stack */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {stagesList.map((st, idx) => {
                const isComplete = activePipelineStage > idx;
                const isCurrent = activePipelineStage === idx;

                return (
                  <div
                    key={idx}
                    style={{
                      background: isCurrent
                        ? 'rgba(249, 115, 22, 0.08)'
                        : isComplete
                        ? 'var(--bg-surface-elevated)'
                        : 'var(--bg-base)',
                      border: '1px solid ' + (isCurrent ? 'var(--accent-saffron)' : isComplete ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'),
                      borderRadius: 'var(--radius-sm)',
                      padding: '16px 20px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'all 0.3s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                      <div
                        style={{
                          width: 34,
                          height: 34,
                          borderRadius: 8,
                          background: isComplete
                            ? 'var(--accent-emerald)'
                            : isCurrent
                            ? 'var(--accent-saffron)'
                            : 'var(--bg-surface)',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: '13px'
                        }}
                      >
                        {isComplete ? <Check size={18} /> : idx + 1}
                      </div>
                      <div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)' }}>
                          {st.title}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {isComplete ? st.detail : isCurrent ? 'Running GPU inference...' : st.desc}
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: '12px', fontWeight: 600 }}>
                      {isComplete ? (
                        <span style={{ color: 'var(--accent-emerald)' }}>✓ Done</span>
                      ) : isCurrent ? (
                        <span style={{ color: 'var(--accent-saffron)' }}>In Progress</span>
                      ) : (
                        <span style={{ color: 'var(--text-faint)' }}>Queued</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* STEP 4: OUTPUT DELIVERY & DUAL VIDEO AUDITION */}
        {currentStep === 4 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', marginBottom: 8 }}>
                  <CheckCircle2 size={14} />
                  <span>QC Passed • Broadcast Grade</span>
                </div>
                <h2 style={{ fontSize: '26px', fontWeight: 800 }}>
                  Dubbed Media Ready for Delivery
                </h2>
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

            {/* Side-by-Side Dual Player Simulation */}
            <div
              className="player-grid"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: 20,
                marginBottom: 32
              }}
            >
              {/* Original Track Card */}
              <div
                style={{
                  background: 'var(--bg-base)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: '14px', fontWeight: 700 }}>Original Video (Hindi)</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Source Track</span>
                </div>
                <div
                  style={{
                    height: 180,
                    borderRadius: 'var(--radius-sm)',
                    background: '#030508',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid var(--border-subtle)',
                    marginBottom: 12,
                    position: 'relative'
                  }}
                >
                  <Film size={36} color="var(--text-faint)" style={{ marginBottom: 8 }} />
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    "नमस्ते छात्रों, आज हम परावर्तन के नियमों को समझेंगे..."
                  </div>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
                  Audio: 150 words/min • Sync Baseline
                </div>
              </div>

              {/* Dubbed Track Card */}
              <div
                style={{
                  background: 'rgba(249, 115, 22, 0.04)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px',
                  border: '1px solid rgba(249, 115, 22, 0.3)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent-saffron)' }}>
                    Nivima Dubbed Video ({auditionLang === 'te' ? 'Telugu • తెలుగు' : 'Tamil • தமிழ்'})
                  </span>
                  <span className="badge-pill" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', padding: '2px 8px' }}>
                    SyncNet 8.7 LSE-C
                  </span>
                </div>
                <div
                  style={{
                    height: 180,
                    borderRadius: 'var(--radius-sm)',
                    background: '#040711',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid rgba(249, 115, 22, 0.25)',
                    marginBottom: 12,
                    position: 'relative'
                  }}
                >
                  {/* Pulsing Audio Bar Equalizer */}
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center', height: 40, marginBottom: 12 }}>
                    {[12, 24, 18, 32, 20, 28, 14, 22, 30, 16].map((h, i) => (
                      <div
                        key={i}
                        className="wave-bar"
                        style={{
                          height: h,
                          animationDelay: `${(i * 0.12).toFixed(2)}s`
                        }}
                      />
                    ))}
                  </div>
                  <div style={{ fontSize: '13px', color: '#f8fafc', fontWeight: 600 }}>
                    {auditionLang === 'te'
                      ? '"నమస్కారం విద్యార్థులారా, ఈరోజు మనం పరావర్తన నియమాలను నేర్చుకుందాం..."'
                      : '"வணக்கம் மாணவர்களே, இன்று நாம் எதிரொளிப்பு விதிகளை கற்போம்..."'}
                  </div>
                </div>

                {/* Audio Track Switcher */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      onClick={() => setAuditionLang('te')}
                      style={{
                        padding: '4px 10px',
                        borderRadius: 4,
                        fontSize: '11px',
                        fontWeight: 700,
                        background: auditionLang === 'te' ? 'var(--accent-saffron)' : 'var(--bg-surface)',
                        color: auditionLang === 'te' ? '#fff' : 'var(--text-muted)',
                        border: '1px solid var(--border-subtle)',
                        cursor: 'pointer'
                      }}
                    >
                      Telugu (తెలుగు)
                    </button>
                    <button
                      onClick={() => setAuditionLang('ta')}
                      style={{
                        padding: '4px 10px',
                        borderRadius: 4,
                        fontSize: '11px',
                        fontWeight: 700,
                        background: auditionLang === 'ta' ? 'var(--accent-saffron)' : 'var(--bg-surface)',
                        color: auditionLang === 'ta' ? '#fff' : 'var(--text-muted)',
                        border: '1px solid var(--border-subtle)',
                        cursor: 'pointer'
                      }}
                    >
                      Tamil (தமிழ்)
                    </button>
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                    Cloned Timbre: 86.4%
                  </span>
                </div>
              </div>
            </div>

            {/* Multitrack Delivery Package Download Links */}
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: 14 }}>
              Production Assets & Download Files
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
              {[
                { name: 'Full Dubbed Video (MP4)', size: '18.4 MB', type: '1080p H.264 + AAC 48kHz' },
                { name: 'Isolated Cloned Vocal (WAV)', size: '12.1 MB', type: '24-bit 48kHz Broadcast' },
                { name: 'Dravidian Subtitles (SRT)', size: '4.2 KB', type: 'UTF-8 Timed Captions' },
                { name: 'Quality Control Audit (JSON)', size: '1.8 KB', type: 'LSE-C 8.7 • PSNR 34.2 dB' }
              ].map((file, i) => (
                <div
                  key={i}
                  style={{
                    background: 'var(--bg-surface-elevated)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '16px',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 700 }}>{file.name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {file.size} • {file.type}
                    </div>
                  </div>
                  <button
                    onClick={() => alert(`Downloading ${file.name}...`)}
                    style={{
                      background: 'var(--accent-saffron)',
                      border: 'none',
                      color: '#fff',
                      padding: '8px',
                      borderRadius: 6,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                    title={`Download ${file.name}`}
                  >
                    <Download size={14} />
                  </button>
                </div>
              ))}
            </div>

            {/* Quick jump to 3DMM Lab and QC */}
            <div style={{ display: 'flex', gap: 12, marginTop: 24, flexWrap: 'wrap' }}>
              {onOpenLab && (
                <button
                  onClick={onOpenLab}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 18px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <ExternalLink size={14} />
                  <span>Inspect 3DMM Facial Visemes</span>
                </button>
              )}
              {onOpenQC && (
                <button
                  onClick={onOpenQC}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 18px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <ExternalLink size={14} />
                  <span>Open Full QC & SyncNet Analytics</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
