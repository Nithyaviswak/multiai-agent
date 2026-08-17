import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, Sparkles, CheckCircle2, ChevronDown, Plus } from 'lucide-react';
import { networkAPI } from '../services/api';

const SUGGESTIONS = [
  'Configure OSPF on core-router-01',
  'Check connectivity between the two routers',
  'Audit security compliance across devices',
  'Why is the edge link flapping tonight?',
  'Summarize the network health report',
];

const ProviderBadge = ({ provider }) => {
  const labels = { groq: 'Groq', openai: 'OpenAI', anthropic: 'Claude', custom: 'Custom' };
  return (
    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-paper-inset text-ink-mute">
      {labels[provider] || provider}
    </span>
  );
};

const FreeBadge = () => (
  <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-[rgba(63,145,66,0.12)] text-[#3F9142]">
    FREE
  </span>
);

const Composer = ({ onStart, isLoading }) => {
  const [intent, setIntent] = useState('');
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [modelOpen, setModelOpen] = useState(false);
  const pickerRef = useRef(null);

  useEffect(() => {
    networkAPI.getModels().then(r => {
      if (r.success) {
        setModels(r.models || []);
        setActiveModel(r.current);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    const close = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) setModelOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (intent.trim() && !isLoading) onStart(intent.trim());
  };

  const pickModel = async (id) => {
    setActiveModel(id);
    setModelOpen(false);
    try {
      const r = await networkAPI.setModel(id);
      if (r.success) setActiveModel(r.model);
    } catch (err) {
      console.error('model switch failed', err);
    }
  };

  const activeMeta = models.find(m => m.id === activeModel);
  const groupByProvider = () => {
    const out = {};
    for (const m of models) {
      (out[m.provider] = out[m.provider] || []).push(m);
    }
    return out;
  };
  const grouped = groupByProvider();

  return (
    <div className="w-full">
      {/* Suggestion chips above composer */}
      {!isLoading && !intent && (
        <div className="flex flex-wrap gap-2 justify-center mb-3 px-1">
          {SUGGESTIONS.map((s, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => setIntent(s)}
              className="px-3.5 py-2 rounded-full bg-paper-elevated border border-paper-line text-[13px] text-ink-soft hover:border-clay/40 hover:text-ink transition-colors"
            >
              {s}
            </motion.button>
          ))}
        </div>
      )}

      {/* Composer bar */}
      <form onSubmit={handleSubmit} className="glass rounded-[2rem] shadow-composer px-3 py-2.5 flex items-end gap-2">
        <div className="flex-1">
          <textarea
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Ask an agent anything…"
            rows={1}
            maxLength={2000}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
            }}
            className="w-full resize-none bg-transparent border-none outline-none text-[15px] leading-relaxed text-ink placeholder:text-ink-faint py-1.5 px-2"
          />
        </div>

        <div className="relative" ref={pickerRef}>
          <button
            type="button"
            onClick={() => setModelOpen(!modelOpen)}
            disabled={isLoading}
            className="flex items-center gap-1.5 pl-2.5 pr-2 py-1.5 rounded-full bg-paper-inset text-ink-soft hover:text-ink transition-colors text-[13px] font-medium"
            title="Change model"
          >
            <Sparkles className="w-3.5 h-3.5 text-clay" />
            <span className="max-w-[120px] truncate">{activeMeta?.name || activeModel || 'Model'}</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${modelOpen ? 'rotate-180' : ''}`} />
          </button>

          <AnimatePresence>
            {modelOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.16 }}
                className="absolute bottom-full right-0 mb-2 w-80 max-h-[70vh] overflow-y-auto rounded-2xl bg-paper-elevated border border-paper-line shadow-elevated p-2 z-30"
              >
                <p className="px-3 pt-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                  Choose a model
                </p>
                {Object.entries(grouped).map(([provider, list]) => (
                  <div key={provider} className="mb-1">
                    <p className="px-3 pt-2 pb-1 text-[11px] font-medium text-ink-mute uppercase tracking-wide">
                      {provider === 'custom' ? 'Your custom models' : provider}
                    </p>
                    {list.map(m => {
                      const configured = m.key_configured;
                      const isActive = m.id === activeModel;
                      return (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => configured && pickModel(m.id)}
                          className={`w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl text-left transition-colors ${
                            isActive ? 'bg-clay-soft' : 'hover:bg-paper-inset'
                          } ${configured ? '' : 'opacity-50 cursor-not-allowed'}`}
                        >
                          <div className="min-w-0">
                            <p className="text-[13px] font-medium text-ink truncate">{m.name}</p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <ProviderBadge provider={m.provider} />
                              {m.custom && (
                                <span className="text-[10px] text-ink-faint truncate max-w-[110px]">
                                  {m.base_url || ''}
                                </span>
                              )}
                              {!configured && (
                                <span className="text-[10px] text-ink-faint">needs API key</span>
                              )}
                              {m.free && <FreeBadge />}
                            </div>
                          </div>
                          {isActive && <CheckCircle2 className="w-4 h-4 text-clay flex-shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                ))}
                <p className="px-3 py-2 text-[11px] text-ink-faint border-t border-paper-line mt-1">
                  Add your own model name + API key in Settings, or pick a built-in provider key.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <motion.button
          whileTap={{ scale: 0.94 }}
          type="submit"
          disabled={!intent.trim() || isLoading}
          className="w-10 h-10 rounded-full flex items-center justify-center bg-clay text-white
                     disabled:opacity-35 disabled:cursor-not-allowed transition-colors hover:bg-clay-deep flex-shrink-0"
          aria-label="Send"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <ArrowUp className="w-5 h-5" />
          )}
        </motion.button>
      </form>

      <p className="text-center text-[11px] text-ink-faint mt-2">
        Multi AI Agent runs your own providers. No training on your data.
      </p>
    </div>
  );
};

export default Composer;