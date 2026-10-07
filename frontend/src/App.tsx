import { useState, useEffect } from 'react';
import './index.css';
import { Navbar } from './components/Navbar.tsx';
import { Hero } from './components/Hero.tsx';
import { DubbingStudio } from './components/DubbingStudio.tsx';
import { PhonemeVisemeLab } from './components/PhonemeVisemeLab.tsx';
import { SpeedInvariantSection } from './components/SpeedInvariantSection.tsx';
import { PatentSection } from './components/PatentSection.tsx';
import { QCInspector } from './components/QCInspector.tsx';
import { ApiSection } from './components/ApiSection.tsx';

type Theme = 'dark' | 'light';

function App() {
  const [theme, setTheme] = useState<Theme>('dark');
  const [activeSection, setActiveSection] = useState<string>('hero');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleNavigate = (sectionId: string) => {
    setActiveSection(sectionId);
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Track active section on scroll
  useEffect(() => {
    const sections = ['hero', 'studio', 'phonemes', 'speed', 'patent', 'qc', 'api'];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-30% 0px -60% 0px' }
    );

    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div>
      <Navbar
        theme={theme}
        onToggleTheme={handleToggleTheme}
        onNavigate={handleNavigate}
        activeSection={activeSection}
      />

      {/* Ambient BG glow */}
      <div
        aria-hidden="true"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: -1,
          background:
            theme === 'dark'
              ? 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(249,115,22,0.06) 0%, transparent 70%), radial-gradient(ellipse 60% 50% at 90% 40%, rgba(139,92,246,0.05) 0%, transparent 60%)'
              : 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(249,115,22,0.03) 0%, transparent 70%)'
        }}
      />

      <Hero
        onLaunchStudio={() => handleNavigate('studio')}
        onExploreVisemes={() => handleNavigate('phonemes')}
      />

      {/* Section dividers with a faint grid */}
      <div className="bg-grid-pattern" style={{ opacity: 0.4 }} />

      <DubbingStudio />

      <div
        style={{
          height: 1,
          background: 'linear-gradient(to right, transparent, var(--border-subtle), transparent)',
          margin: '0 60px'
        }}
      />

      <PhonemeVisemeLab />

      <div
        style={{
          height: 1,
          background: 'linear-gradient(to right, transparent, var(--border-subtle), transparent)',
          margin: '0 60px'
        }}
      />

      <SpeedInvariantSection />

      <div
        style={{
          height: 1,
          background: 'linear-gradient(to right, transparent, var(--border-subtle), transparent)',
          margin: '0 60px'
        }}
      />

      <PatentSection />

      <div
        style={{
          height: 1,
          background: 'linear-gradient(to right, transparent, var(--border-subtle), transparent)',
          margin: '0 60px'
        }}
      />

      <QCInspector />

      <div
        style={{
          height: 1,
          background: 'linear-gradient(to right, transparent, var(--border-subtle), transparent)',
          margin: '0 60px'
        }}
      />

      <ApiSection />

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '36px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
          background: 'var(--bg-surface)'
        }}
      >
        <div>
          <div style={{ fontSize: '18px', fontWeight: 800, marginBottom: 4 }}>
            <span className="text-gradient-neural">Nivima</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
            Neural Indian Video Interface & Multilingual Animation Platform • Patent-Pending IP
          </div>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-faint)', textAlign: 'right' }}>
          <div>Utility Patent Application Drafted under 35 U.S.C. § 111 & Indian Patent Act 1970</div>
          <div>© 2026 Manoj (GCET Hyderabad) • MIT Licensed Research Platform</div>
        </div>
      </footer>
    </div>
  );
}

export default App;
