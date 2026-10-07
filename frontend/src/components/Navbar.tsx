import React from 'react';
import { Sparkles, Moon, Sun, Github, Terminal } from 'lucide-react';

interface NavbarProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onNavigate: (sectionId: string) => void;
  activeSection: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  theme,
  onToggleTheme,
  onNavigate,
  activeSection
}) => {
  return (
    <nav
      className="glass-panel"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        padding: '14px 28px',
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
        onClick={() => onNavigate('hero')}
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
              fontSize: '20px',
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

      {/* Nav items */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        {[
          { id: 'studio', label: 'Dubbing Studio' },
          { id: 'phonemes', label: 'Retroflex Viseme Lab' },
          { id: 'speed', label: 'Speed-Invariant 2×' },
          { id: 'patent', label: 'Patent & IP' },
          { id: 'qc', label: 'QC Gatekeeper' },
          { id: 'api', label: 'API & Python SDK' }
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            style={{
              background: activeSection === item.id ? 'var(--bg-surface-elevated)' : 'transparent',
              color: activeSection === item.id ? 'var(--accent-saffron)' : 'var(--text-muted)',
              border: activeSection === item.id ? '1px solid var(--border-highlight)' : '1px solid transparent',
              padding: '8px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.18s ease'
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-main)',
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {theme === 'dark' ? <Sun size={17} color="#fbbf24" /> : <Moon size={17} color="#6366f1" />}
        </button>

        {/* GitHub link */}
        <a
          href="https://github.com/manoj-1407/nivima"
          target="_blank"
          rel="noreferrer"
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-main)',
            height: 36,
            padding: '0 12px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            textDecoration: 'none',
            fontSize: '13px',
            fontWeight: 600,
            transition: 'all 0.2s'
          }}
        >
          <Github size={16} />
          <span>Star on GitHub</span>
        </a>

        {/* CTA Launch Studio */}
        <button
          onClick={() => onNavigate('studio')}
          style={{
            background: 'linear-gradient(135deg, var(--accent-saffron), #ea580c)',
            border: 'none',
            color: '#fff',
            height: 36,
            padding: '0 16px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: 'var(--glow-saffron)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Terminal size={15} />
          <span>Launch Studio</span>
        </button>
      </div>
    </nav>
  );
};
