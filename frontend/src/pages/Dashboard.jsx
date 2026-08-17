import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import { Settings2, Shield, CheckCircle, AlertTriangle, RefreshCw, Sparkles } from 'lucide-react';
import Composer from '../components/NetworkInput';
import AgentProgress from '../components/AgentProgress';
import NetworkResults from '../components/NetworkResults';
import SettingsPanel from '../components/SettingsPanel';
import { useNetworkAutomation } from '../hooks/useResearch';
import { networkAPI } from '../services/api';

const muted = '#8A8474';
const brand = '#D97757';

const Dashboard = () => {
  const { state, startWorkflow, resetWorkflow, approveAction } = useNetworkAutomation();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentModel, setCurrentModel] = useState(null);

  useEffect(() => {
    networkAPI.getCurrentModel().then(r => {
      if (r.success) setCurrentModel(r.model || null);
    }).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-paper text-ink flex flex-col">
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: '#FBFAF7',
            color: '#3D3929',
            border: '1px solid #E0DBD0',
            borderRadius: '1rem',
            fontFamily: 'Inter, sans-serif',
            fontSize: '13px',
          },
        }}
      />

      {/* Header */}
      <header className="sticky top-0 z-30 glass border-b border-paper-line flex-shrink-0">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-[1.1rem] bg-clay flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-serif text-[17px] leading-none tracking-tight">Multi&nbsp;AI&nbsp;Agent</h1>
              <p className="text-[10px] text-ink-mute mt-0.5">Provider-agnostic agentic platform</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {currentModel && (
              <button
                onClick={() => setSettingsOpen(true)}
                className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-paper-inset text-ink-soft text-[12px] font-medium hover:text-ink transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" style={{ color: brand }} />
                <span className="max-w-[140px] truncate">{currentModel.name}</span>
              </button>
            )}
            <button
              onClick={() => setSettingsOpen(true)}
              className="w-9 h-9 rounded-full flex items-center justify-center text-ink-soft hover:text-ink hover:bg-paper-inset transition-colors"
              aria-label="Settings"
            >
              <Settings2 className="w-[18px] h-[18px]" />
            </button>
          </div>
        </div>
      </header>

      {/* Scrollable content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col gap-5">
          {/* Hero / empty state */}
          {(!state.data && !state.error && !state.isLoading) && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
              className="pt-8 pb-2 text-center"
            >
              <div className="w-16 h-16 mx-auto mb-4 rounded-[1.6rem] bg-clay-soft flex items-center justify-center rotate-3">
                <Sparkles className="w-7 h-7 text-clay" />
              </div>
              <h2 className="font-serif text-[28px] leading-tight text-balance">
                Ask a multi-agent team<br />to get things done
              </h2>
              <p className="text-[13.5px] text-ink-soft mt-3 max-w-md mx-auto leading-relaxed">
                Specialized agents plan, analyze, configure, verify, and summarize — using your own API keys and models.
              </p>
              <div className="mt-5 flex items-center justify-center gap-2">
                {['Plan', 'Act', 'Verify', 'Summarize'].map((t, i) => (
                  <motion.span
                    key={t}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + i * 0.06 }}
                    className="px-3 py-1 rounded-full bg-paper-elevated border border-paper-line text-[11px] font-medium text-ink-soft"
                  >
                    {t}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          )}

          {/* Progress */}
          <AnimatePresence mode="wait">
            {state.isLoading && state.workflowId && (
              <motion.div
                key="progress"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.35 }}
              >
                <AgentProgress currentStep={state.currentStep} errors={state.data?.errors} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Approval */}
          <AnimatePresence>
            {state.data?.current_step === 'awaiting_approval' && (
              <motion.div
                key="approval"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className="card p-5"
              >
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-full bg-[rgba(176,96,0,0.12)] flex items-center justify-center flex-shrink-0">
                    <Shield className="w-5 h-5" style={{ color: '#B06000' }} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-[15px] font-semibold" style={{ color: '#B06000' }}>Human approval required</h3>
                    <p className="text-[12.5px] text-ink-soft mt-1 mb-4">
                      This action would change device state. Approve to continue or deny to stop.
                    </p>
                    <div className="flex items-center gap-2.5">
                      <button onClick={() => approveAction(state.workflowId, true)} className="btn btn-success">
                        <CheckCircle className="w-4 h-4" /> Approve &amp; continue
                      </button>
                      <button onClick={() => approveAction(state.workflowId, false)} className="btn btn-danger">
                        <AlertTriangle className="w-4 h-4" /> Deny
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results */}
          <AnimatePresence mode="wait">
            {(state.data || state.error) && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.35 }}
                className="space-y-4"
              >
                <NetworkResults data={state.data} isLoading={state.isLoading} />

                {state.error && !state.isLoading && (
                  <div className="card p-5">
                    <div className="flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-full bg-[rgba(197,82,63,0.12)] flex items-center justify-center flex-shrink-0">
                        <AlertTriangle className="w-5 h-5 text-[#C5523F]" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-[15px] font-semibold text-[#C5523F]">Workflow failed</h3>
                        <p className="text-[12.5px] text-ink-soft mt-1 mb-3">{state.error}</p>
                        <button onClick={resetWorkflow} className="btn btn-secondary">
                          <RefreshCw className="w-4 h-4" /> Retry
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer */}
          <footer className="pt-2 pb-6 text-center">
            <p className="text-[11px]" style={{ color: muted }}>
              <span className="font-semibold">Multi AI Agent</span> · your keys, your models
            </p>
          </footer>
        </div>
      </main>

      {/* Bottom composer */}
      <div className="flex-shrink-0 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2">
        <div className="max-w-3xl mx-auto">
          <Composer onStart={startWorkflow} isLoading={state.isLoading} />
        </div>
      </div>

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
};

export default Dashboard;