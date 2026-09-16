import { motion } from 'framer-motion';
import { Home, Briefcase, Compass, User } from 'lucide-react';

const ITEMS = [
  { id: 'explore', label: 'Home', icon: Home },
  { id: 'trips', label: 'Trips', icon: Briefcase },
  { id: 'plan', label: 'Plan', icon: Compass },
  { id: 'settings', label: 'Profile', icon: User },
];

const BottomNav = ({ view, onNavigate, onPlan, onSettings }) => {
  const handle = (item) => {
    if (item.id === 'plan') onPlan?.();
    else if (item.id === 'settings') onSettings?.();
    else onNavigate(item.id);
  };

  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-40 md:hidden glass border-t border-paper-line pb-safe"
      aria-label="Mobile navigation"
    >
      <div className="grid grid-cols-4 h-16">
        {ITEMS.map(item => {
          const Icon = item.icon;
          const active = view === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handle(item)}
              className="relative flex flex-col items-center justify-center gap-1 text-ink-mute"
              aria-label={item.label}
              aria-current={active ? 'page' : undefined}
            >
              <Icon className={`w-[22px] h-[22px] transition-colors ${active ? 'text-primary' : ''}`} strokeWidth={active ? 2.2 : 1.8} />
              <span className={`text-[10.5px] font-medium ${active ? 'text-primary' : ''}`}>{item.label}</span>
              {active && (
                <motion.span
                  layoutId="bottom-nav-dot"
                  className="absolute -bottom-0 w-1 h-1 rounded-full bg-primary"
                  transition={{ duration: 0.25 }}
                />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNav;