import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Moon,
  Sun,
  Mic,
  Activity,
  Layers,
  FileText,
  Code2,
  Terminal,
  Menu,
  X,
  Cpu,
  CheckCircle2
} from 'lucide-react';

export type PageTab = 'studio' | 'lab' | 'speed' | 'qc' | 'patent' | 'api' | 'guide';

interface NavbarProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  activeTab: PageTab;
  onSelectTab: (tab: PageTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  theme,
  onToggleTheme,
  activeTab,
  onSelectTab
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<{
    connected: boolean;
    gpuName?: string;
    vram?: number;
  }>({ connected: false });

  // Poll backend system info
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch('/api/v1/system/info');
        if (res.ok) {
          const data = await res.json();
          setBackendStatus({
            connected: true,
            gpuName: data.gpu_name || 'NVIDIA RTX 3070',
            vram: data.vram_total_gb || 8.0
          });
        } else {
          setBackendStatus({ connected: false });
        }
      } catch {
        setBackendStatus({ connected: false });
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems: { id: PageTab; label: string; icon: React.ReactNode }[] = [
    { id: 'studio', label: 'Dubbing Studio', icon: <Mic size={15} /> },
    { id: 'lab', label: '3DMM Viseme Lab', icon: <Layers size={15} /> },
    { id: 'speed', label: 'Speed Invariance', icon: <Activity size={15} /> },
    { id: 'qc', label: 'QC & SyncNet', icon: <CheckCircle2 size={15} /> },
    { id: 'patent', label: 'Patent & IP', icon: <FileText size={15} /> },
    { id: 'api', label: 'API Console', icon: <Code2 size={15} /> },
    { id: 'guide', label: '3070 Setup Guide', icon: <Terminal size={15} /> }
  ];

  const handleTabClick = (tab: PageTab) => {
    onSelectTab(tab);
    setMobileMenuOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <nav
        className="glass-panel"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'all 0.2s ease',
          borderBottom: '1px solid var(--border-subtle)'
        }}
      >
        {/* Brand logo */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer'
          }}
          onClick={() => handleTabClick('studio')}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, var(--accent-saffron), var(--accent-violet))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--glow-saffron)'
            }}
          >
            <Sparkles size={20} color="#fff" />
          </div>
          <div>
            <div
              style={{
                fontSize: '19px',
                fontWeight: 800,
                letterSpacing: '-0.03em',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span className="text-gradient-neural">Nivima</span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'rgba(249, 115, 22, 0.15)',
                  color: 'var(--accent-saffron)',
                  border: '1px solid rgba(249, 115, 22, 0.3)',
                  fontWeight: 700
                }}
              >
                v1.0 RESEARCH
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500, lineHeight: 1 }}>
              Neural Indic Video & Animation
            </div>
          </div>
        </div>

        {/* Desktop Navigation Tabs */}
        <div
          className="desktop-nav"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: 'var(--bg-surface-elevated)',
            padding: '4px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)'
          }}
        >
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-tab-btn ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => handleTabClick(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Right Action Icons & Telemetry */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Hardware / Backend Status Pill */}
          <div
            className="badge-pill"
            style={{
              background: backendStatus.connected
                ? 'rgba(16, 185, 129, 0.12)'
                : 'rgba(245, 158, 11, 0.12)',
              border: `1px solid ${backendStatus.connected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              color: backendStatus.connected ? 'var(--accent-emerald)' : 'var(--accent-saffron)',
              cursor: 'pointer'
            }}
            onClick={() => handleTabClick('guide')}
            title={backendStatus.connected ? 'Backend API connected' : 'Click to see 3070 setup guide'}
          >
            <Cpu size={13} />
            <span style={{ fontSize: '11px' }}>
              {backendStatus.connected
                ? `RTX 3070 (${backendStatus.vram}GB) • Online`
                : 'GPU Standalone Mode'}
            </span>
          </div>

          {/* Theme toggle */}
          <button
            onClick={onToggleTheme}
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface-elevated)',
              color: 'var(--text-main)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>

          {/* Mobile hamburger menu button */}
          <button
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              width: 38,
              height: 38,
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface-elevated)',
              color: 'var(--text-main)',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile Slide-Over Drawer */}
      {mobileMenuOpen && (
        <div
          style={{
            position: 'fixed',
            top: 61,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 99,
            background: 'rgba(6, 8, 13, 0.95)',
            backdropFilter: 'blur(20px)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-faint)', textTransform: 'uppercase', marginBottom: 6, fontWeight: 700 }}>
            Navigate Workstation
          </div>
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 18px',
                borderRadius: 'var(--radius-md)',
                fontSize: '15px',
                fontWeight: activeTab === item.id ? 700 : 500,
                border: '1px solid ' + (activeTab === item.id ? 'var(--accent-saffron)' : 'var(--border-subtle)'),
                background: activeTab === item.id ? 'rgba(249, 115, 22, 0.15)' : 'var(--bg-surface-elevated)',
                color: activeTab === item.id ? 'var(--accent-saffron)' : 'var(--text-main)',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}

          <div
            style={{
              marginTop: 'auto',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              fontSize: '12px',
              color: 'var(--text-muted)'
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: 4 }}>
              Nivima Indic Platform
            </div>
            Speed-invariant lip synchronization for 10 Indian languages. Fully optimized for desktop and mobile devices.
          </div>
        </div>
      )}
    </>
  );
};
