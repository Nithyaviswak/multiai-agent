import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, KeyRound, Eye, EyeOff, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { networkAPI } from '../services/api';

const PROVIDER_META = {
  groq: { label: 'Groq', tip: 'console.groq.com — free tier available', placeholder: 'gsk_…' },
  openai: { label: 'OpenAI', tip: 'platform.openai.com/api-keys', placeholder: 'sk-…' },
  anthropic: { label: 'Anthropic', tip: 'console.anthropic.com/settings/keys', placeholder: 'sk-ant-…' },
};

const SettingsPanel = ({ open, onClose }) => {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [keys, setKeys] = useState({});
  const [show, setShow] = useState({});

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    networkAPI.getProviders()
      .then(r => { if (r.success) setProviders(r.providers || []); })
      .catch(() => toast.error('Could not load providers'))
      .finally(() => setLoading(false));
  }, [open]);

  const save = async (provider) => {
    const val = (keys[provider] || '').trim();
    if (!val) { toast.error('Enter an API key first'); return; }
    setSaving(s => ({ ...s, [provider]: true }));
    try {
      const r = await networkAPI.setProviderKey(provider, val);
      if (r.success) {
        toast.success(`${(PROVIDER_META[provider] || {}).label || provider} key saved`);
        setKeys(k => ({ ...k, [provider]: '' }));
        const provs = await networkAPI.getProviders();
        if (provs.success) setProviders(provs.providers || []);
      } else {
        toast.error(r.error || 'Failed to save key');
      }
    } catch (e) {
      toast.error('Failed to save key: ' + e.message);
    } finally {
      setSaving(s => ({ ...s, [provider]: false }));
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-ink-soft/40 z-40"
          />
          <motion.div
            initial={{ opacity: 0, y: 32, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 32, scale: 0.98 }}
            transition={{ duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
            className="fixed inset-x-0 bottom-0 sm:inset-x-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 w-full sm:w-[28rem] bg-paper-elevated rounded-t-[2rem] sm:rounded-[2rem] shadow-elevated border border-paper-line z-50 max-h-[88vh] flex flex-col"
          >
            <div className="px-5 pt-4 pb-3 flex items-center justify-between border-b border-paper-line flex-shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-clay-soft flex items-center justify-center">
                  <KeyRound className="w-4 h-4 text-clay" />
                </div>
                <div>
                  <h2 className="text-[15px] font-semibold text-ink">API Keys</h2>
                  <p className="text-[11px] text-ink-mute">Run models with your own providers</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full flex items-center justify-center text-ink-mute hover:bg-paper-inset transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
              {loading ? (
                <div className="flex flex-col items-center gap-2 py-8 text-ink-mute">
                  <Loader2 className="w-5 h-5 animate-spin text-clay" />
                  <span className="text-xs">Loading providers…</span>
                </div>
              ) : (
                providers.map(p => {
                  const meta = PROVIDER_META[p.name] || { label: p.name, tip: '', placeholder: '' };
                  const configured = p.configured;
                  return (
                    <div key={p.name} className="rounded-2xl border border-paper-line bg-paper/60 p-3.5">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-ink">{meta.label || p.name}</span>
                          {configured ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-[#3F9142] bg-[rgba(63,145,66,0.12)] px-2 py-0.5 rounded-full">
                              <CheckCircle2 className="w-3 h-3" /> Connected
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-ink-faint bg-paper-inset px-2 py-0.5 rounded-full">
                              <Sparkles className="w-3 h-3" /> Needs key
                            </span>
                          )}
                        </div>
                        {(p.models || 0) > 0 && <span className="text-[10px] text-ink-faint">{p.models} models</span>}
                      </div>
                      <p className="text-[11px] text-ink-mute mb-2">{meta.tip}</p>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <input
                            type={show[p.name] ? 'text' : 'password'}
                            value={keys[p.name] || ''}
                            onChange={e => setKeys(k => ({ ...k, [p.name]: e.target.value }))}
                            placeholder={configured ? 'Replace key…' : meta.placeholder}
                            className="input pr-10 text-xs"
                          />
                          <button
                            onClick={() => setShow(s => ({ ...s, [p.name]: !s[p.name] }))}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-mute hover:text-ink transition-colors"
                          >
                            {show[p.name] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        <button
                          onClick={() => save(p.name)}
                          disabled={saving[p.name] || !(keys[p.name] || '').trim()}
                          className="btn btn-primary flex-shrink-0 py-2"
                        >
                          {saving[p.name] ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                          Save
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
              <p className="text-center text-[11px] text-ink-faint pt-1">
                Keys stay on this server and are never sent to any other provider.
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;