import { useState, useEffect } from 'react';
import './index.css';
import { Navbar, PageTab } from './components/Navbar.tsx';
import { Hero } from './components/Hero.tsx';
import { DubbingStudio } from './components/DubbingStudio.tsx';
import { PhonemeVisemeLab } from './components/PhonemeVisemeLab.tsx';
import { SpeedInvariantSection } from './components/SpeedInvariantSection.tsx';
import { PatentSection } from './components/PatentSection.tsx';
import { QCInspector } from './components/QCInspector.tsx';
import { ApiSection } from './components/ApiSection.tsx';
import { ExecutionGuide } from './components/ExecutionGuide.tsx';

type Theme = 'dark' | 'light';

function App() {
  const [theme, setTheme] = useState<Theme>('dark');
  const [activeTab, setActiveTab] = useState<PageTab>('studio');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleSelectTab = (tab: PageTab) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        theme={theme}
        onToggleTheme={handleToggleTheme}
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
      />

      {/* Ambient background glow */}
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

      <div className="bg-grid-pattern" style={{ opacity: 0.35, position: 'fixed', inset: 0, zIndex: -2 }} />

      {/* Main Tab Content */}
      <main style={{ flex: 1 }}>
        {activeTab === 'studio' && (
          <div>
            <Hero
              onLaunchStudio={() => {
                const el = document.getElementById('studio');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
              onExploreVisemes={() => handleSelectTab('lab')}
            />
            <div id="studio">
              <DubbingStudio
                onOpenLab={() => handleSelectTab('lab')}
                onOpenQC={() => handleSelectTab('qc')}
              />
            </div>
          </div>
        )}

        {activeTab === 'lab' && (
          <div style={{ padding: '20px 0' }}>
            <PhonemeVisemeLab />
          </div>
        )}

        {activeTab === 'speed' && (
          <div style={{ padding: '20px 0' }}>
            <SpeedInvariantSection />
          </div>
        )}

        {activeTab === 'qc' && (
          <div style={{ padding: '20px 0' }}>
            <QCInspector />
          </div>
        )}

        {activeTab === 'patent' && (
          <div style={{ padding: '20px 0' }}>
            <PatentSection />
          </div>
        )}

        {activeTab === 'api' && (
          <div style={{ padding: '20px 0' }}>
            <ApiSection />
          </div>
        )}

        {activeTab === 'guide' && (
          <div style={{ padding: '20px 0' }}>
            <ExecutionGuide />
          </div>
        )}
      </main>

      {/* Production Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '30px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
          background: 'var(--bg-surface)'
        }}
      >
        <div>
          <div style={{ fontSize: '17px', fontWeight: 800, marginBottom: 4 }}>
            <span className="text-gradient-neural">Nivima</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
            Neural Indian Video Interface & Multilingual Animation Platform • Patent-Pending Architecture
          </div>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-faint)', textAlign: 'right' }}>
          <div>Utility Patent Application Drafted under Indian Patent Act 1970 & 35 U.S.C. § 111</div>
          <div>© 2026 Manoj (GCET Hyderabad) • MIT Licensed Research Platform</div>
        </div>
      </footer>
    </div>
  );
}

export default App;
