import { motion } from 'framer-motion';
import { KeyRound, User, ShieldCheck, Sparkles } from 'lucide-react';
import EnterprisePanel from '../components/EnterprisePanel';
import ThemeToggle from '../components/ThemeToggle';

const ProfilePage = ({ currentModel, onOpenSettings, theme, onToggleTheme, workflowId }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.35 }}
    className="max-w-3xl mx-auto pt-10 pb-10 px-4 sm:px-0"
  >
    <div className="flex items-center gap-3 mb-6">
      <div className="w-11 h-11 rounded-2xl bg-primary-soft flex items-center justify-center">
        <User className="w-5 h-5 text-primary" />
      </div>
      <div>
        <h1 className="font-serif text-[34px] leading-none tracking-tight">Profile</h1>
        <p className="text-[13px] text-ink-soft mt-1.5">Your keys, your models, your platform</p>
      </div>
    </div>

    <div className="space-y-3 mb-3">
      <button
        onClick={onOpenSettings}
        className="w-full rounded-2xl border border-paper-line bg-paper-elevated p-4 text-left hover:border-ink-faint transition-colors group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-paper-inset flex items-center justify-center">
              <KeyRound className="w-4 h-4 text-secondary" />
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink">Models &amp; API keys</p>
              <p className="text-[11.5px] text-ink-mute">
                {currentModel ? `Using ${currentModel.name || currentModel}` : 'Bring your own keys and models'}
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-primary-soft text-primary text-[11px] font-semibold group-hover:bg-primary group-hover:text-white transition-colors">
            Manage <Sparkles className="w-3 h-3" />
          </span>
        </div>
      </button>

      <div className="rounded-2xl border border-paper-line bg-paper-elevated p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-paper-inset flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-warning" />
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink">Appearance</p>
              <p className="text-[11.5px] text-ink-mute">Switch between light and dark</p>
            </div>
          </div>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </div>

    <div className="mb-6">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-mute mb-2.5 flex items-center gap-1.5">
        <Sparkles className="w-3 h-3 text-primary" /> AI agent platform
      </p>
      <EnterprisePanel workflowId={workflowId} />
    </div>
  </motion.div>
);

export default ProfilePage;