import { useCallback, useEffect, useState } from 'react';

const KEY = 'multiai.theme';

const getStored = () => {
  try {
    const v = localStorage.getItem(KEY);
    if (v === 'light' || v === 'dark') return v;
  } catch {}
  if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)')?.matches) {
    return 'dark';
  }
  return 'light';
};

export const useTheme = () => {
  const [theme, setTheme] = useState(getStored);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    try { localStorage.setItem(KEY, theme); } catch {}
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0B1322' : '#F6F5F2');
  }, [theme]);

  const toggle = useCallback(() => setTheme(t => (t === 'dark' ? 'light' : 'dark')), []);

  return { theme, toggle, isDark: theme === 'dark' };
};