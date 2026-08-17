import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import {
  Activity, AlertTriangle, CheckCircle, Shield, Mail, Github, Linkedin, RefreshCw
} from 'lucide-react';
import NetworkInput from '../components/NetworkInput';
import AgentProgress from '../components/AgentProgress';
import NetworkResults from '../components/NetworkResults';
import EnterprisePanel from '../components/EnterprisePanel';
import { useNetworkAutomation } from '../hooks/useResearch';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] } },
};

const Dashboard = () => {
  const { state, startWorkflow, resetWorkflow, approveAction } = useNetworkAutomation();

  return (
    <div className="min-h-screen bg-[#0b0f1a] bg-grid">
      <div className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 50% -20%, rgba(99, 102, 241, 0.06), transparent 60%)'
        }}
      />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a2332',
            color: '#f1f5f9',
            border: '1px solid rgba(99, 102, 241, 0.15)',
            borderRadius: '0.75rem',
            fontFamily: 'Inter, sans-serif',
          },
        }}
      />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        <motion.header variants={itemVariants} className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[rgba(99,102,241,0.1)] border border-[rgba(99,102,241,0.15)] text-xs text-[#818cf8] font-medium mb-4">
            <Activity className="w-3.5 h-3.5" />
            Enterprise-Grade &middot; 12 AI Agents &middot; Real-Time
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-3">
            <span className="gradient-text">Multi-Agent AI</span>
            <br />
            <span className="text-white">Network Automation</span>
          </h1>
          <p className="text-lg text-[#94a3b8] max-w-2xl mx-auto leading-relaxed">
            Orchestrate network operations with 12 specialized AI agents &mdash; tool calling, memory systems, human approval, RBAC, and real-time monitoring.
          </p>
        </motion.header>

        <motion.div variants={itemVariants}>
          <NetworkInput onStart={startWorkflow} isLoading={state.isLoading} />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-6">
          <div className="lg:col-span-3 space-y-6">
            <AnimatePresence mode="wait">
              {state.isLoading && state.workflowId && (
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4 }}
                >
                  <AgentProgress currentStep={state.currentStep} errors={state.data?.errors} />
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence mode="wait">
              {(state.data || state.error) && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4 }}
                >
                  <NetworkResults data={state.data} isLoading={state.isLoading} />
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {state.data?.current_step === 'awaiting_approval' && (
                <motion.div
                  key="approval"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="card p-6 border-l-4 border-l-[#f59e0b]"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-[rgba(245,158,11,0.15)] flex items-center justify-center flex-shrink-0">
                      <Shield className="w-5 h-5 text-[#fbbf24]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-[#fbbf24] mb-1">Human Approval Required</h3>
                      <p className="text-sm text-[#94a3b8] mb-4">
                        This configuration action requires your approval before it can be applied to network devices.
                      </p>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => approveAction(state.workflowId, true)}
                          className="btn btn-success"
                        >
                          <CheckCircle className="w-4 h-4" />
                          Approve &amp; Continue
                        </button>
                        <button
                          onClick={() => approveAction(state.workflowId, false)}
                          className="btn btn-danger"
                        >
                          <AlertTriangle className="w-4 h-4" />
                          Deny
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {state.error && !state.isLoading && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="card p-6 border-l-4 border-l-[#ef4444]"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-[rgba(239,68,68,0.15)] flex items-center justify-center flex-shrink-0">
                      <AlertTriangle className="w-5 h-5 text-[#f87171]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-[#f87171] mb-1">Workflow Failed</h3>
                      <p className="text-sm text-[#94a3b8] mb-4">{state.error}</p>
                      <button onClick={resetWorkflow} className="btn btn-danger">
                        <RefreshCw className="w-4 h-4" />
                        Retry Workflow
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="lg:col-span-1">
            <motion.div variants={itemVariants}>
              <EnterprisePanel workflowId={state.workflowId} />
            </motion.div>
          </div>
        </div>

        <motion.footer
          variants={itemVariants}
          className="mt-16 pt-8 border-t border-[rgba(255,255,255,0.04)] text-center"
        >
          <p className="text-sm text-[#64748b] mb-3">
            Developed by <span className="font-semibold text-[#f1f5f9]">R NITHYANANDACHARI</span>
          </p>
          <div className="flex items-center justify-center gap-6 text-sm">
            {[
              { label: 'Email', href: 'mailto:nviswaks@gmail.com', icon: Mail },
              { label: 'GitHub', href: 'https://github.com/Nithyaviswak', icon: Github },
              { label: 'LinkedIn', href: 'https://www.linkedin.com/in/nithyananda1311', icon: Linkedin },
            ].map(({ label, href, icon: Icon }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-[#64748b] hover:text-[#818cf8] transition-colors duration-200"
              >
                <Icon className="w-4 h-4" />
                {label}
              </a>
            ))}
          </div>
        </motion.footer>
      </motion.div>
    </div>
  );
};

export default Dashboard;
