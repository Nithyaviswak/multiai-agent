import { motion } from 'framer-motion';
import { CheckCircle, Clock, AlertCircle, Terminal, Globe, Zap, Cpu, FileText, Shield, Activity, Bot, Sparkles } from 'lucide-react';

const AGENT_STEPS = [
  { id: 'plan', label: 'Planner', icon: Terminal },
  { id: 'topology', label: 'Topology Discovery', icon: Bot },
  { id: 'knowledge', label: 'Knowledge Agent', icon: Globe },
  { id: 'netconf', label: 'NETCONF Collection', icon: Activity },
  { id: 'configuration', label: 'Configuration', icon: Zap },
  { id: 'automation', label: 'Automation', icon: Cpu },
  { id: 'verification', label: 'Verification', icon: CheckCircle },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
  { id: 'compliance', label: 'Compliance', icon: Shield },
  { id: 'log_analysis', label: 'Log Analysis', icon: FileText },
  { id: 'incident_response', label: 'Incident Response', icon: AlertCircle },
  { id: 'report', label: 'Report Generator', icon: Sparkles },
  { id: 'complete', label: 'Complete', icon: CheckCircle },
];

const AgentProgress = ({ currentStep, errors }) => {
  const getStepStatus = (stepId) => {
    if (stepId === currentStep) return 'current';
    const idx = AGENT_STEPS.findIndex(s => s.id === stepId);
    const cur = AGENT_STEPS.findIndex(s => s.id === currentStep);
    if (idx < cur) return 'completed';
    return 'pending';
  };

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[13px] font-semibold text-ink flex items-center gap-2">
          <Bot className="w-4 h-4 text-clay" />
          Agent workflow
        </h3>
        <span className="text-[10px] text-ink-mute">
          {AGENT_STEPS.findIndex(s => s.id === currentStep) + 1 || 0}/{AGENT_STEPS.length - 1} steps
        </span>
      </div>

      <div className="relative">
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-paper-inset" />
        <div className="space-y-0.5">
          {AGENT_STEPS.filter(s => s.id !== 'complete').map((step, index) => {
            const Icon = step.icon;
            const status = getStepStatus(step.id);
            const isCurrent = status === 'current';
            const isCompleted = status === 'completed';
            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className={`flex items-center gap-3 py-2 px-2.5 rounded-xl transition-all duration-300 ${
                  isCurrent ? 'bg-clay-soft' : isCompleted ? 'bg-[rgba(63,145,66,0.05)]' : ''
                }`}
              >
                <div className={`relative z-10 w-[22px] h-[22px] rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                  isCompleted ? 'bg-[#3F9142]' : isCurrent ? 'bg-clay' : 'bg-paper-inset'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="w-3.5 h-3.5 text-white" />
                  ) : isCurrent ? (
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}>
                      <Clock className="w-3 h-3 text-white" />
                    </motion.div>
                  ) : (
                    <Icon className="w-3 h-3 text-ink-mute" />
                  )}
                </div>
                <span className={`text-[12.5px] font-medium transition-colors duration-300 ${
                  isCurrent ? 'text-clay-deep' : isCompleted ? 'text-[#3F9142]' : 'text-ink-mute'
                }`}>
                  {step.label}
                </span>
                {isCurrent && (
                  <motion.span
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="ml-auto text-[9px] font-semibold px-2 py-0.5 rounded-full bg-clay text-white flex-shrink-0"
                  >
                    Active
                  </motion.span>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {errors && errors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 p-3 rounded-xl bg-[rgba(197,82,63,0.08)] border border-[rgba(197,82,63,0.15)]"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-[#C5523F] mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-[#C5523F]">Errors detected</p>
              <p className="text-[11px] text-ink-soft mt-0.5">{errors[0]}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AgentProgress;