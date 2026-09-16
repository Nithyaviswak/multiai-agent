import { motion } from 'framer-motion';
import { Check, AlertTriangle, Users } from 'lucide-react';
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

const TeamRecap = ({ currentStep, failedSteps = [], details = {} }) => (
  <div className="space-y-1">
    <div className="flex items-center gap-2 mb-2">
      <div className="w-8 h-8 rounded-xl bg-primary-soft flex items-center justify-center">
        <Users className="w-4 h-4 text-primary" />
      </div>
      <div>
        <p className="text-[13px] font-semibold text-ink">AI travel team</p>
        <p className="text-[10.5px] text-ink-mute">{AGENTS.length} specialists worked on this plan</p>
      </div>
    </div>

    {AGENTS.map(agent => {
      const Icon = agent.icon;
      const status = statusOf(agent, currentStep, failedSteps);
      const meta = STATUS_META[status];
      return (
        <motion.div
          key={agent.id}
          initial={{ opacity: 0, x: -6 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
          className="flex items-center gap-2.5 py-1.5"
        >
          <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${
            status === 'complete' ? 'bg-success/12 text-success' : status === 'attention' ? 'bg-warning/12 text-warning' : 'bg-paper-inset text-ink-mute'
          }`}>
            {status === 'complete' ? <Check className="w-3.5 h-3.5" strokeWidth={2.4} /> : <Icon className="w-3 h-3" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-medium text-ink truncate">{agent.name}</p>
            <p className="text-[10.5px] text-ink-faint truncate">{details[agent.id] || agent.task}</p>
          </div>
          {status === 'attention' && <AlertTriangle className="w-3 h-3 text-warning flex-shrink-0" />}
          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot} flex-shrink-0`} aria-label={meta.label} />
        </motion.div>
      );
    })}
  </div>
);

export default TeamRecap;