import { motion } from 'framer-motion';
import { Settings2, Sparkles } from 'lucide-react';
import Logo from './Logo';
import ThemeToggle from './ThemeToggle';

const Header = ({ view, onNavigate, theme, onToggleTheme, onOpenSettings, currentModel }) => {
  const nav = [
    { id: 'explore', label: 'Explore' },
    { id: 'trips', label: 'My Trips' },
  ];

  return (
    <header className="sticky top-0 z-40 glass border-b border-paper-line">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        <button
          onClick={() => onNavigate('explore')}
          className="flex items-center gap-2.5 rounded-lg"
          aria-label="Go to home"
        >
          <Logo />
        </button>

        <nav className="hidden md:flex items-center gap-1" aria-label="Primary">
          {nav.map(item => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`px-3.5 py-1.5 rounded-full text-[13.5px] font-medium transition-colors ${
                view === item.id ? 'bg-primary-soft text-primary' : 'text-ink-soft hover:text-ink'
              }`}
              aria-current={view === item.id ? 'page' : undefined}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-1.5">
          {currentModel && (
            <button
              onClick={onOpenSettings}
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-paper-inset text-ink-soft text-[12px] font-medium hover:text-ink transition-colors"
              title="Model & settings"
            >
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              <span className="max-w-[140px] truncate">{currentModel.name || currentModel}</span>
            </button>
          )}
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          <button
            onClick={onOpenSettings}
            className="w-9 h-9 rounded-full flex items-center justify-center text-ink-soft hover:text-ink hover:bg-paper-inset transition-colors"
            aria-label="Open settings"
          >
            <Settings2 className="w-[18px] h-[18px]" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;