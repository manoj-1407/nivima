import React, { useState } from 'react';
import {
  Cpu,
  Copy,
  Check,
  HardDrive,
  Zap,
  RefreshCw
} from 'lucide-react';

export const ExecutionGuide: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [pingStatus, setPingStatus] = useState<string | null>(null);
  const [isPinging, setIsPinging] = useState(false);

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handlePingBackend = async () => {
    setIsPinging(true);
    setPingStatus('Testing connection to http://localhost:8000...');
    try {
      const res = await fetch('/api/v1/system/info');
      if (res.ok) {
        const data = await res.json();
        setPingStatus(`✓ Online! GPU: ${data.gpu_name} (${data.vram_total_gb}GB VRAM) • CUDA: ${data.cuda_version || 'Ready'} • FFmpeg: ${data.ffmpeg_available ? 'Detected' : 'Missing'}`);
      } else {
        setPingStatus('⚠ Server responded with error ' + res.status);
      }
    } catch {
      setPingStatus('✗ Cannot connect to localhost:8000. Start backend using: uvicorn src.api.main:app --port 8000');
    } finally {
      setIsPinging(false);
    }
  };

  const steps = [
    {
      title: '1. Setup & CUDA PyTorch Installation',
      desc: 'Activate Python virtual environment and install PyTorch with CUDA 12.1 for the RTX 3070.',
      code: `# Windows PowerShell:\npython -m venv venv\n.\\venv\\Scripts\\Activate.ps1\npip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121\npip install -r requirements.txt -r requirements-dev.txt`
    },
    {
      title: '2. Verify GPU & Environment',
      desc: 'Run the automated checker to verify your 8GB VRAM, CUDA drivers, and FFmpeg.',
      code: `python scripts/check_environment.py`
    },
    {
      title: '3. Pre-Cache Model Weights (Optional)',
      desc: 'Pre-download Whisper large-v3, IndicTrans2, XTTS-v2, and Demucs so execution never stalls mid-run.',
      code: `python scripts/download_models.py`
    },
    {
      title: '4. Run Local Video Dubbing Test (Phase 1)',
      desc: 'Execute real dubbing on a Hindi video into Telugu and Tamil directly on the RTX 3070.',
      code: `python scripts/run_phase1_demo.py --video sample_hindi.mp4 --source hi --targets te ta --output ./output_demo`
    },
    {
      title: '5. Launch API Server & Interactive Studio',
      desc: 'Start the FastAPI backend with live hardware telemetry, then access the Studio in your browser.',
      code: `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`
    }
  ];

  return (
    <div style={{ maxWidth: 1050, margin: '0 auto', padding: '40px 20px 100px' }}>
      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
        <div
          className="badge-pill"
          style={{
            background: 'rgba(249, 115, 22, 0.12)',
            border: '1px solid rgba(249, 115, 22, 0.3)',
            color: 'var(--accent-saffron)',
            marginBottom: 12
          }}
        >
          <Cpu size={14} />
          <span>NVIDIA RTX 3070 Execution Manual</span>
        </div>
        <h1 style={{ fontSize: '34px', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
          Step-by-Step Testing & Deployment Guide
        </h1>
        <p style={{ color: 'var(--text-muted)', maxWidth: 680, margin: '0 auto', fontSize: '15px' }}>
          Everything you need to verify, benchmark, and run real Hindi-to-Telugu/Tamil dubbing on your RTX 3070 (8GB VRAM) machine.
        </p>
      </div>

      {/* Backend Health Check Card */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          marginBottom: 32,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(249, 115, 22, 0.08))'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <Zap size={18} color="var(--accent-saffron)" />
            <span style={{ fontSize: '16px', fontWeight: 700 }}>Live Hardware Connectivity Probe</span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            {pingStatus ? pingStatus : 'Click to test real-time connectivity to your local FastAPI backend.'}
          </div>
        </div>
        <button
          onClick={handlePingBackend}
          disabled={isPinging}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 18px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-saffron)',
            color: '#fff',
            border: 'none',
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={14} className={isPinging ? 'animate-spin' : ''} />
          <span>{isPinging ? 'Pinging...' : 'Test Backend Connection'}</span>
        </button>
      </div>

      {/* VRAM Budget Table for RTX 3070 (8GB) */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '28px',
          marginBottom: 36
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <HardDrive size={20} color="var(--accent-violet)" />
          <h2 style={{ fontSize: '18px', fontWeight: 700 }}>RTX 3070 (8GB VRAM) Memory Allocation</h2>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: 20 }}>
          The Nivima pipeline executes model stages sequentially, ensuring peak VRAM stays well within your 8GB hardware limit:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {[
            { stage: '1. Demucs Stem Separation', vram: '2.1 GB', time: '~8–12 sec', note: 'Separates speech & background music' },
            { stage: '2. Faster-Whisper ASR', vram: '2.8 GB', time: '~3–5 sec', note: 'large-v3 model with word timestamps' },
            { stage: '3. IndicTrans2 Translation', vram: '1.2 GB', time: '~2–4 sec', note: 'Hindi → Telugu / Tamil / Bengali' },
            { stage: '4. Coqui XTTS / IndicTTS', vram: '3.0 GB', time: '~15–20 sec', note: 'Voice clone + Dravidian synthesis' }
          ].map((item, i) => (
            <div
              key={i}
              style={{
                background: 'var(--bg-surface-elevated)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: 4 }}>{item.stage}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: '11px', color: 'var(--accent-saffron)', fontWeight: 700 }}>Peak VRAM: {item.vram}</span>
                <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 600 }}>{item.time}</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.note}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Step by Step Execution Instructions */}
      <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 20 }}>
        Step-by-Step Command Walkthrough
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {steps.map((st, idx) => (
          <div
            key={idx}
            className="glass-panel"
            style={{
              borderRadius: 'var(--radius-md)',
              padding: '24px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: 4 }}>{st.title}</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{st.desc}</p>
              </div>
              <button
                onClick={() => copyToClipboard(st.code, idx)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                {copiedIndex === idx ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
                <span>{copiedIndex === idx ? 'Copied!' : 'Copy Command'}</span>
              </button>
            </div>

            <pre
              style={{
                background: 'var(--bg-base)',
                padding: '14px 18px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                color: '#e2e8f0',
                overflowX: 'auto',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <code>{st.code}</code>
            </pre>
          </div>
        ))}
      </div>

      {/* Troubleshooting Checklist */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 'var(--radius-lg)',
          padding: '28px',
          marginTop: 36
        }}
      >
        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: 16 }}>
          Frequently Encountered Questions on RTX 3070
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-saffron)', marginBottom: 2 }}>
              • What if I get CUDA Out of Memory (OOM)?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Set <code>WHISPER_COMPUTE_TYPE=int8_float16</code> in your <code>.env</code> file. Each pipeline step cleans up memory before starting the next.
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-saffron)', marginBottom: 2 }}>
              • How do I access the UI from another device on the same local Wi-Fi?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Start uvicorn with <code>--host 0.0.0.0</code>. Open <code>http://&lt;your-3070-local-ip&gt;:8000</code> in your phone or laptop browser. The responsive mobile interface will adapt automatically.
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent-saffron)', marginBottom: 2 }}>
              • Where do the output dubbed videos get saved?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              When running the CLI, outputs are saved in the <code>--output ./output_demo/</code> folder. When running the Studio UI, files can be downloaded directly from the delivery dashboard.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
