import { motion } from 'framer-motion';
import {
  CheckCircle, Clock, AlertCircle, Server, Activity, Shield,
  FileText, Zap, Globe, Cpu, Users, Terminal, Network
} from 'lucide-react';

const AGENT_STEPS = [
  { id: 'plan', label: 'Planner', icon: Terminal, color: '#6366f1' },
  { id: 'topology', label: 'Topology Discovery', icon: Server, color: '#06b6d4' },
  { id: 'knowledge', label: 'Knowledge Agent', icon: Globe, color: '#10b981' },
  { id: 'netconf', label: 'NETCONF Collection', icon: Activity, color: '#6366f1' },
  { id: 'configuration', label: 'Configuration', icon: Zap, color: '#f59e0b' },
  { id: 'automation', label: 'Automation', icon: Cpu, color: '#8b5cf6' },
  { id: 'verification', label: 'Verification', icon: CheckCircle, color: '#10b981' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity, color: '#06b6d4' },
  { id: 'compliance', label: 'Compliance', icon: Shield, color: '#ef4444' },
  { id: 'log_analysis', label: 'Log Analysis', icon: FileText, color: '#f59e0b' },
  { id: 'incident_response', label: 'Incident Response', icon: AlertCircle, color: '#ef4444' },
  { id: 'report', label: 'Report Generator', icon: FileText, color: '#8b5cf6' },
  { id: 'complete', label: 'Complete', icon: CheckCircle, color: '#10b981' },
];

const AgentProgress = ({ currentStep, errors }) => {
  const getStepStatus = (stepId) => {
    if (stepId === currentStep) return 'current';
    const stepIndex = AGENT_STEPS.findIndex(s => s.id === stepId);
    const currentIndex = AGENT_STEPS.findIndex(s => s.id === currentStep);
    if (stepIndex < currentIndex) return 'completed';
    return 'pending';
  };

  const hasError = errors && errors.length > 0;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-semibold text-[#e2e8f0] flex items-center gap-2">
          <Network className="w-4 h-4 text-[#818cf8]" />
          12-Agent Workflow
        </h3>
        <span className="text-xs text-[#64748b]">
          {AGENT_STEPS.findIndex(s => s.id === currentStep) + 1 || 0}/{AGENT_STEPS.length - 1} agents
        </span>
      </div>

      <div className="relative">
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-[rgba(99,102,241,0.1)]" />

        <div className="space-y-0.5">
          {AGENT_STEPS.filter(s => s.id !== 'complete').map((step, index) => {
            const status = getStepStatus(step.id);
            const isCurrent = status === 'current';
            const isCompleted = status === 'completed';

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className={`relative flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-300 ${
                  isCurrent
                    ? 'bg-[rgba(99,102,241,0.08)]'
                    : isCompleted
                    ? 'bg-[rgba(16,185,129,0.04)]'
                    : ''
                }`}
              >
                <div className={`relative z-10 w-[22px] h-[22px] rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                  isCompleted
                    ? 'bg-[#10b981]'
                    : isCurrent
                    ? 'bg-[#6366f1]'
                    : 'bg-[rgba(255,255,255,0.06)]'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="w-3.5 h-3.5 text-white" />
                  ) : isCurrent ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    >
                      <Clock className="w-3 h-3 text-white" />
                    </motion.div>
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-[#64748b]" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <span className={`text-xs font-medium transition-colors duration-300 ${
                    isCurrent ? 'text-[#818cf8]' : isCompleted ? 'text-[#34d399]' : 'text-[#64748b]'
                  }`}>
                    {step.label}
                  </span>
                </div>

                {isCurrent && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex-shrink-0"
                  >
                    <span className="badge badge-primary text-[10px] px-2 py-0.5">Active</span>
                  </motion.div>
                )}
                {isCompleted && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex-shrink-0"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-[#34d399]" />
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {hasError && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-4 p-3 rounded-lg bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.15)]"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-[#f87171] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-[#f87171]">Errors detected</p>
              <p className="text-[10px] text-[#94a3b8] mt-0.5">{errors[0]}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AgentProgress;
