import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, KeyRound, Eye, EyeOff, CheckCircle2, Loader2, Sparkles,
  Plus, Trash2, Link2, ShieldCheck
} from 'lucide-react';
import toast from 'react-hot-toast';
import { networkAPI } from '../services/api';

const PROVIDER_META = {
  groq: { label: 'Groq', tip: 'console.groq.com — free open-source models (GPT-OSS, Qwen, Compound).', placeholder: 'gsk_…' },
  openai: { label: 'OpenAI', tip: 'platform.openai.com/api-keys', placeholder: 'sk-…' },
  anthropic: { label: 'Anthropic', tip: 'console.anthropic.com/settings/keys', placeholder: 'sk-ant-…' },
};

const BASE_URL_PRESETS = [
  { label: 'OpenRouter (free models)', url: 'https://openrouter.ai/api/v1', example: 'meta-llama/llama-3.3-70b-instruct:free' },
  { label: 'Groq', url: 'https://api.groq.com/openai/v1', example: 'llama-3.3-70b-versatile' },
  { label: 'Together AI', url: 'https://api.together.xyz/v1', example: 'meta-llama/Llama-3.3-70B-Instruct-Turbo' },
  { label: 'Mistral', url: 'https://api.mistral.ai/v1', example: 'open-mistral-7b' },
  { label: 'Ollama (local)', url: 'http://localhost:11434/v1', example: 'llama3.2' },
  { label: 'OpenAI', url: 'https://api.openai.com/v1', example: 'gpt-4o-mini' },
];

const Field = ({ label, children }) => (
  <label className="block">
    <span className="text-[11px] font-medium text-ink-mute uppercase tracking-wide">{label}</span>
    <div className="mt-1">{children}</div>
  </label>
);

const ProviderCard = ({ p, keys, setKeys, show, setShow, saving, save }) => {
  const meta = PROVIDER_META[p.name] || { label: p.name, tip: '', placeholder: '' };
  const configured = p.configured;
  return (
    <div className="rounded-2xl border border-paper-line bg-paper/60 p-3.5">
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
};

const SettingsPanel = ({ open, onClose, onChanged }) => {
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [keys, setKeys] = useState({});
  const [show, setShow] = useState({});

  // "Add a model" form: name + API key (+ base URL for custom endpoints).
  const [formOpen, setFormOpen] = useState(false);
  const [formName, setFormName] = useState('');
  const [formModelId, setFormModelId] = useState('');
  const [formApiKey, setFormApiKey] = useState('');
  const [formBaseUrl, setFormBaseUrl] = useState(BASE_URL_PRESETS[0].url);
  const [formPreset, setFormPreset] = useState(0);
  const [formShowKey, setFormShowKey] = useState(false);
  const [adding, setAdding] = useState(false);

  const refresh = () => {
    setLoading(true);
    Promise.all([networkAPI.getProviders(), networkAPI.getModels()])
      .then(([p, m]) => {
        if (p.success) setProviders(p.providers || []);
        if (m.success) setModels(m.models || []);
      })
      .catch(() => toast.error('Could not load settings'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!open) return;
    refresh();
    networkAPI.getBaseUrls().then(r => {
      if (r.success && r.base_urls) {
        const presets = Object.entries(r.base_urls).map(([label, url]) => ({ label, url, example: '' }));
        if (presets.length) {
          setFormPreset(0);
          setFormBaseUrl(presets[0].url);
          setPresets(presets);
        }
      }
    }).catch(() => {});
  }, [open]);

  const [presets, setPresets] = useState(BASE_URL_PRESETS);

  const saveProvider = async (provider) => {
    const val = (keys[provider] || '').trim();
    if (!val) { toast.error('Enter an API key first'); return; }
    setSaving(s => ({ ...s, [provider]: true }));
    try {
      const r = await networkAPI.setProviderKey(provider, val);
      if (r.success) {
        toast.success(`${(PROVIDER_META[provider] || {}).label || provider} key saved`);
        setKeys(k => ({ ...k, [provider]: '' }));
        refresh();
        onChanged && onChanged();
      } else {
        toast.error(r.error || 'Failed to save key');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to save key');
    } finally {
      setSaving(s => ({ ...s, [provider]: false }));
    }
  };

  const addModel = async () => {
    const mid = formModelId.trim();
    if (!formName.trim() || !mid) { toast.error('Enter a model name and model ID'); return; }
    if (!formApiKey.trim()) { toast.error('Enter the API key for this model'); return; }
    setAdding(true);
    try {
      const r = await networkAPI.addCustomModel(formName.trim(), mid, formApiKey.trim(), formBaseUrl);
      if (r.success) {
        toast.success(`Added ${r.model.name}`);
        setFormName(''); setFormModelId(''); setFormApiKey('');
        setFormOpen(false);
        refresh();
        onChanged && onChanged();
      } else {
        toast.error(r.error || 'Failed to add model');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add model');
    } finally {
      setAdding(false);
    }
  };

  const removeModel = async (mid) => {
    try {
      const r = await networkAPI.removeCustomModel(mid);
      if (r.success) {
        toast.success('Model removed');
        refresh();
        onChanged && onChanged();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to remove model');
    }
  };

  const customModels = models.filter(m => m.custom);
  const builtinByProvider = providerName =>
    models.filter(m => !m.custom && m.provider === providerName).length;
  const providersWithCount = providers.map(p => ({ ...p, models: builtinByProvider(p.name) }));

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
            className="fixed inset-x-0 bottom-0 sm:inset-x-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 w-full sm:w-[30rem] bg-paper-elevated rounded-t-[2rem] sm:rounded-[2rem] shadow-elevated border border-paper-line z-50 max-h-[90vh] flex flex-col"
          >
            <div className="px-5 pt-4 pb-3 flex items-center justify-between border-b border-paper-line flex-shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-clay-soft flex items-center justify-center">
                  <KeyRound className="w-4 h-4 text-clay" />
                </div>
                <div>
                  <h2 className="text-[15px] font-semibold text-ink">Models &amp; API Keys</h2>
                  <p className="text-[11px] text-ink-mute">Bring your own keys and models</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full flex items-center justify-center text-ink-mute hover:bg-paper-inset transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {/* Your custom models */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[13px] font-semibold text-ink flex items-center gap-1.5">
                    <Link2 className="w-3.5 h-3.5 text-clay" /> Your models
                  </h3>
                  <button
                    onClick={() => setFormOpen(o => !o)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-clay-soft text-clay-deep text-[11px] font-medium hover:bg-clay/20 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add model
                  </button>
                </div>

                {loading ? (
                  <div className="flex flex-col items-center gap-2 py-6 text-ink-mute">
                    <Loader2 className="w-5 h-5 animate-spin text-clay" />
                    <span className="text-xs">Loading…</span>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {customModels.length === 0 && !formOpen && (
                      <p className="text-[12px] text-ink-faint bg-paper-inset/60 rounded-xl px-3 py-2.5">
                        Add any model by name + API key — OpenRouter free models, Together, Mistral, local Ollama, and more.
                      </p>
                    )}

                    {customModels.map(m => (
                      <div key={m.id} className="flex items-center justify-between gap-2 rounded-xl border border-paper-line bg-paper/60 px-3 py-2.5">
                        <div className="min-w-0">
                          <p className="text-[13px] font-medium text-ink truncate">{m.name}</p>
                          <p className="text-[10px] text-ink-mute truncate">{m.id}</p>
                          <p className="text-[10px] text-ink-faint truncate">{m.base_url}</p>
                        </div>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {m.key_configured && (
                            <span className="inline-flex items-center gap-1 text-[9px] font-medium text-[#3F9142] bg-[rgba(63,145,66,0.12)] px-2 py-0.5 rounded-full">
                              <ShieldCheck className="w-3 h-3" /> key set
                            </span>
                          )}
                          <button
                            onClick={() => removeModel(m.id)}
                            className="w-7 h-7 rounded-full flex items-center justify-center text-ink-mute hover:text-[#C5523F] hover:bg-[rgba(197,82,63,0.08)] transition-colors"
                            title="Remove model"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}

                    {formOpen && (
                      <div className="rounded-xl border border-clay/30 bg-clay-soft/40 p-3 space-y-2.5 animate-slide-down">
                        <Field label="Model name">
                          <input
                            value={formName}
                            onChange={e => setFormName(e.target.value)}
                            placeholder="e.g. Llama 3.3 70B (free)"
                            className="input text-xs"
                          />
                        </Field>
                        <Field label="Model ID">
                          <input
                            value={formModelId}
                            onChange={e => setFormModelId(e.target.value)}
                            placeholder={presets[formPreset]?.example || 'model-id'}
                            className="input text-xs font-mono"
                          />
                        </Field>
                        <Field label="API base URL">
                          <div className="flex gap-1.5 flex-wrap mb-1.5">
                            {presets.map((pr, i) => (
                              <button
                                key={pr.label}
                                type="button"
                                onClick={() => { setFormPreset(i); setFormBaseUrl(pr.url); }}
                                className={`px-2 py-1 rounded-full text-[10px] font-medium transition-colors ${
                                  formPreset === i
                                    ? 'bg-clay text-white'
                                    : 'bg-paper-inset text-ink-soft hover:text-ink'
                                }`}
                              >
                                {pr.label}
                              </button>
                            ))}
                          </div>
                          <input
                            value={formBaseUrl}
                            onChange={e => { setFormBaseUrl(e.target.value); setFormPreset(-1); }}
                            className="input text-xs font-mono"
                            placeholder="https://api.openai.com/v1"
                          />
                        </Field>
                        <Field label="API key">
                          <div className="relative">
                            <input
                              type={formShowKey ? 'text' : 'password'}
                              value={formApiKey}
                              onChange={e => setFormApiKey(e.target.value)}
                              placeholder="sk-…"
                              className="input text-xs pr-10"
                            />
                            <button
                              onClick={() => setFormShowKey(s => !s)}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-mute hover:text-ink transition-colors"
                            >
                              {formShowKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          </div>
                        </Field>
                        <div className="flex gap-2 pt-1">
                          <button onClick={addModel} disabled={adding} className="btn btn-primary flex-1 py-2 text-xs">
                            {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            Add model &amp; key
                          </button>
                          <button onClick={() => setFormOpen(false)} className="btn btn-secondary py-2 text-xs">
                            Cancel
                          </button>
                        </div>
                        <p className="text-[10px] text-ink-faint">
                          Keys are stored in memory on this server only.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Provider keys */}
              <div>
                <h3 className="text-[13px] font-semibold text-ink flex items-center gap-1.5 mb-2">
                  <KeyRound className="w-3.5 h-3.5 text-clay" /> Provider keys
                </h3>
                <div className="space-y-2">
                  {loading ? (
                    <div className="flex flex-col items-center gap-2 py-6 text-ink-mute">
                      <Loader2 className="w-5 h-5 animate-spin text-clay" />
                      <span className="text-xs">Loading…</span>
                    </div>
                  ) : (
                    providersWithCount.map(p => (
                      <ProviderCard
                        key={p.name}
                        p={p}
                        keys={keys}
                        setKeys={setKeys}
                        show={show}
                        setShow={setShow}
                        saving={saving}
                        save={saveProvider}
                      />
                    ))
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;