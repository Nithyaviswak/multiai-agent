import { Sun, Moon } from 'lucide-react';

const ThemeToggle = ({ theme, onToggle }) => (
  <button
    onClick={onToggle}
    aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
    className="w-9 h-9 rounded-full flex items-center justify-center text-ink-soft hover:text-ink hover:bg-paper-inset transition-colors"
  >
    {theme === 'dark' ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
  </button>
);

export default ThemeToggle;