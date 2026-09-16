import { motion } from 'framer-motion';
import { Check, AlertTriangle } from 'lucide-react';
import { AGENTS, STATUS_META } from '../data/agents';

const statusOf = (agent, currentStep, failedSteps) => {
  if (failedSteps.includes(agent.id)) return 'attention';
  if (currentStep === 'complete' || currentStep === 'error') return 'complete';
  if (agent.id === currentStep) return 'working';
  const curI = AGENTS.findIndex(a => a.id === currentStep);
  const thisI = AGENTS.findIndex(a => a.id === agent.id);
  if (curI >= 0 && thisI < curI) return 'complete';
  return 'waiting';
};

const AgentCard = ({ agent, status, detail, index }) => {
  const Icon = agent.icon;
  const meta = STATUS_META[status];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className={`flex items-start gap-3 rounded-2xl p-3.5 border transition-colors duration-300 ${
        status === 'working'
          ? 'bg-primary-soft/60 border-primary/30'
          : status === 'complete'
            ? 'bg-paper-elevated border-paper-line'
            : 'bg-paper-elevated/60 border-paper-line'
      }`}
    >
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors ${
        status === 'working' ? 'bg-primary text-white' :
        status === 'complete' ? 'bg-success/15 text-success' :
        status === 'attention' ? 'bg-warning/15 text-warning' :
        'bg-paper-inset text-ink-mute'
      }`}>
        {status === 'complete' ? <Check className="w-4.5 h-4.5" strokeWidth={2.4} /> : <Icon className="w-[18px] h-[18px]" strokeWidth={1.9} />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-[13.5px] font-semibold text-ink truncate">{agent.name}</p>
          {status === 'attention' && <AlertTriangle className="w-3.5 h-3.5 text-warning flex-shrink-0" />}
        </div>
        <p className={`text-[11.5px] mt-0.5 ${status === 'waiting' ? 'text-ink-faint' : 'text-ink-soft'}`}>
          {detail || agent.task}
        </p>
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot} ${status === 'working' ? 'animate-pulse-soft' : ''}`} />
          <span className={`text-[10px] font-medium uppercase tracking-wider ${meta.text}`}>{meta.label}</span>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * The AI travel team. `currentStep`, `seenSteps` and `failedSteps` come from the
 * live workflow poll; when a detail map is provided (e.g. "Found 6 restaurants")
 * it replaces the default task text for completed agents.
 */
const AgentTeam = ({ currentStep, failedSteps = [], details = {}, className = '' }) => (
  <div className={`grid grid-cols-1 sm:grid-cols-2 gap-2 ${className}`}>
    {AGENTS.map((agent, i) => (
      <AgentCard
        key={agent.id}
        agent={agent}
        index={i}
        status={statusOf(agent, currentStep, failedSteps)}
        detail={details[agent.id]}
      />
    ))}
  </div>
);

export default AgentTeam;